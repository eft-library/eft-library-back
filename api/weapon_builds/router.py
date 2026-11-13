import logging
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from api.weapon_builds.contracts import OPTIONAL_AUTH, error_responses
from api.weapon_builds.schemas import (
    BuildCommentPage, BuildResponse, BuildVersion, CopyBuild, CreateBuild, CreateBuildComment,
    CreatedComment, DeletedResource, OwnBuildPage, PublicationRevision, PublicBuildPage,
    PublishedBuild, UpdateBuild, UpdateBuildComment, UpdatedComment, VoteResult, Workspace,
)
from api.weapon_builds.service import BuildService
from database import Database
from util.auth import BearerToken, verify_google_access_token
from util.http_exceptions import HttpError

logger=logging.getLogger(__name__)
def prevent_caching(response: Response):
    response.headers['Cache-Control']='private, no-store'
    response.headers['Vary']='Authorization'


router=APIRouter(prefix='/v3/builds',tags=['User Weapon Builds'],dependencies=[Depends(prevent_caching)])
bearer=BearerToken(tokenUrl='token',auto_error=False)


def get_session():
    try:
        with Database.SessionLocal() as session:
            session.execute(text("SET LOCAL statement_timeout='10s'"))
            session.execute(text("SET LOCAL lock_timeout='5s'"))
            try:
                yield session
                session.commit()
            except BaseException:
                session.rollback()
                raise
    except SQLAlchemyError:
        logger.exception('User build transaction failed')
        raise HttpError.BUILD_STORAGE_UNAVAILABLE.exception() from None


# Commit (including deferred FK checks) must complete before sending a success response.
SessionDependency=Annotated[Session,Depends(get_session,scope='function')]


def get_actor(session: SessionDependency, token: Annotated[str|None,Depends(bearer)]):
    if token is None:
        return None
    email=verify_google_access_token(token)
    row=session.execute(text('select email,nickname,is_admin from user_info where email=:email'),{'email':email}).mappings().one_or_none()
    if row is None:
        raise HttpError.BUILD_REGISTERED_USER_REQUIRED.exception()
    return dict(row)


def require_actor(actor: Annotated[dict|None,Depends(get_actor)]):
    if actor is None:
        raise HttpError.LOGIN_REQUIRED.exception(headers={'WWW-Authenticate':'Bearer'})
    return actor


Actor=Annotated[dict|None,Depends(get_actor)]
RequiredActor=Annotated[dict,Depends(require_actor)]
Page=Annotated[int,Query(ge=1,le=1_000_000)]
Size=Annotated[int,Query(ge=1,le=100)]


def success(data):
    return {'status':200,'msg':'OK','data':data}


@router.get('',response_model=BuildResponse[PublicBuildPage],responses=error_responses())
def discover_builds(session: SessionDependency, weapon_item_id: str|None=Query(None,min_length=1,max_length=200),
                    word: str=Query('',max_length=200),sort: Literal['latest','best']='latest',
                    period: Literal['week','month','all']='month',page: Page=1,page_size: Size=20):
    return success(BuildService.discover(session,weapon_item_id,word,sort,period,page,page_size))


@router.get('/mine',response_model=BuildResponse[OwnBuildPage],responses=error_responses(authentication=True))
def my_builds(session: SessionDependency,actor: RequiredActor,page: Page=1,page_size: Size=20,
              word: str=Query('',max_length=200),
              weapon_item_id: str|None=Query(None,min_length=1,max_length=200)):
    return success(BuildService.mine(session,actor,page,page_size,word,weapon_item_id))


@router.post('',response_model=BuildResponse[Workspace],responses=error_responses(
    HttpError.MODDING_WEAPON_NOT_FOUND,HttpError.MODDING_ITEM_NOT_FOUND,
    HttpError.BUILD_REQUEST_CONFLICT,HttpError.BUILD_LIMIT_REACHED,authentication=True))
def create_build(body: CreateBuild,session: SessionDependency,actor: RequiredActor):
    return success(BuildService.create(session,actor,body))


@router.get('/{build_id}',response_model=BuildResponse[Workspace|PublishedBuild],
    openapi_extra=OPTIONAL_AUTH,responses=error_responses(HttpError.BUILD_NOT_FOUND,authentication=True))
def get_user_build(build_id: UUID,session: SessionDependency,actor: Actor,view: Literal['draft','published']='published'):
    return success(BuildService.detail(session,actor,build_id,view))


@router.put('/{build_id}',response_model=BuildResponse[Workspace],responses=error_responses(
    HttpError.BUILD_NOT_FOUND,HttpError.MODDING_WEAPON_NOT_FOUND,HttpError.MODDING_ITEM_NOT_FOUND,
    HttpError.BUILD_VERSION_CONFLICT,authentication=True))
def update_build(build_id: UUID,body: UpdateBuild,session: SessionDependency,actor: RequiredActor):
    return success(BuildService.update(session,actor,build_id,body))


@router.delete('/{build_id}',response_model=BuildResponse[DeletedResource],responses=error_responses(
    HttpError.BUILD_NOT_FOUND,HttpError.BUILD_VERSION_CONFLICT,authentication=True))
def delete_build(build_id: UUID,session: SessionDependency,actor: RequiredActor,
                  expected_version: int=Query(ge=1)):
    return success(BuildService.delete(session,actor,build_id,expected_version))


@router.post('/{build_id}/publication',response_model=BuildResponse[Workspace],responses=error_responses(
    HttpError.BUILD_NOT_FOUND,HttpError.BUILD_VERSION_CONFLICT,authentication=True))
def publish_build(build_id: UUID,body: BuildVersion,session: SessionDependency,actor: RequiredActor):
    return success(BuildService.publish(session,actor,build_id,body.expected_version))


@router.delete('/{build_id}/publication',response_model=BuildResponse[Workspace],responses=error_responses(
    HttpError.BUILD_NOT_FOUND,HttpError.BUILD_VERSION_CONFLICT,authentication=True))
def withdraw_build(build_id: UUID,session: SessionDependency,actor: RequiredActor,
                    expected_version: int=Query(ge=1)):
    return success(BuildService.withdraw(session,actor,build_id,expected_version))


@router.post('/{build_id}/copy',response_model=BuildResponse[Workspace],responses=error_responses(
    HttpError.BUILD_NOT_FOUND,HttpError.BUILD_REVISION_CONFLICT,HttpError.BUILD_REQUEST_CONFLICT,
    HttpError.BUILD_LIMIT_REACHED,authentication=True))
def copy_build(build_id: UUID,body: CopyBuild,session: SessionDependency,actor: RequiredActor):
    return success(BuildService.copy(session,actor,build_id,body))


@router.put('/{build_id}/vote',response_model=BuildResponse[VoteResult],responses=error_responses(
    HttpError.BUILD_NOT_FOUND,HttpError.BUILD_REVISION_CONFLICT,HttpError.BUILD_SELF_VOTE_FORBIDDEN,authentication=True))
def vote_build(build_id: UUID,body: PublicationRevision,session: SessionDependency,actor: RequiredActor):
    return success(BuildService.vote(session,actor,build_id,body.revision,True))


@router.delete('/{build_id}/vote',response_model=BuildResponse[VoteResult],responses=error_responses(
    HttpError.BUILD_NOT_FOUND,HttpError.BUILD_REVISION_CONFLICT,HttpError.BUILD_SELF_VOTE_FORBIDDEN,authentication=True))
def unvote_build(build_id: UUID,session: SessionDependency,actor: RequiredActor,revision: int=Query(ge=1)):
    return success(BuildService.vote(session,actor,build_id,revision,False))


@router.get('/{build_id}/comments',response_model=BuildResponse[BuildCommentPage],
    openapi_extra=OPTIONAL_AUTH,responses=error_responses(
        HttpError.BUILD_NOT_FOUND,HttpError.BUILD_REVISION_CONFLICT,authentication=True))
def get_build_comments(build_id: UUID,session: SessionDependency,actor: Actor,page: Page=1,page_size: Size=20,
                       revision: int|None=Query(None,ge=1,description='Expected current public revision; mismatch returns 409')):
    return success(BuildService.comments(session,actor,build_id,page,page_size,revision))


@router.post('/{build_id}/comments',response_model=BuildResponse[CreatedComment],responses=error_responses(
    HttpError.BUILD_NOT_FOUND,HttpError.BUILD_REVISION_CONFLICT,HttpError.BUILD_REQUEST_CONFLICT,
    HttpError.BUILD_COMMENT_RATE_LIMITED,authentication=True))
def create_build_comment(build_id: UUID,body: CreateBuildComment,session: SessionDependency,actor: RequiredActor):
    return success(BuildService.add_comment(session,actor,build_id,body))


@router.put('/{build_id}/comments/{comment_id}',response_model=BuildResponse[UpdatedComment],responses=error_responses(
    HttpError.BUILD_NOT_FOUND,HttpError.BUILD_COMMENT_NOT_FOUND,HttpError.BUILD_VERSION_CONFLICT,
    HttpError.BUILD_REVISION_CONFLICT,authentication=True))
def update_build_comment(build_id: UUID,comment_id: UUID,body: UpdateBuildComment,session: SessionDependency,actor: RequiredActor):
    return success(BuildService.edit_comment(session,actor,build_id,comment_id,body.expected_version,body.content))


@router.delete('/{build_id}/comments/{comment_id}',response_model=BuildResponse[DeletedResource],responses=error_responses(
    HttpError.BUILD_NOT_FOUND,HttpError.BUILD_COMMENT_NOT_FOUND,HttpError.BUILD_VERSION_CONFLICT,authentication=True))
def delete_build_comment(build_id: UUID,comment_id: UUID,session: SessionDependency,actor: RequiredActor,
                          expected_version: int=Query(ge=1)):
    return success(BuildService.edit_comment(session,actor,build_id,comment_id,expected_version))

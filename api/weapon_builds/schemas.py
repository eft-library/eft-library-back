import json
from datetime import datetime
from typing import Annotated, Any, Generic, Literal, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from api.modding.schemas import ItemSummary

NodeId = Annotated[str, Field(pattern=r'^[A-Za-z0-9_-]{1,80}$')]


class BuildNodeInput(BaseModel):
    node_id: NodeId
    parent_node_id: NodeId | None = None
    slot_id: str | None = Field(None, min_length=1, max_length=200)
    item_id: str = Field(min_length=1, max_length=200)
    attributes: dict[str, Any] | None = None


class BuildContent(BaseModel):
    weapon_item_id: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=120)
    description: str = Field('', max_length=5000)
    nodes: list[BuildNodeInput] = Field(min_length=1, max_length=200)

    @field_validator('title')
    @classmethod
    def clean_title(cls, value):
        value = value.strip()
        if not value:
            raise ValueError('title cannot be blank')
        return value

    @model_validator(mode='after')
    def valid_tree(self):
        if len(json.dumps(self.model_dump(mode='json'), ensure_ascii=False, allow_nan=False).encode()) > 262144:
            raise ValueError('build exceeds 256 KiB')
        nodes = {node.node_id:node for node in self.nodes}
        if len(nodes) != len(self.nodes):
            raise ValueError('duplicate node_id')
        roots = [n for n in self.nodes if n.parent_node_id is None]
        if len(roots) != 1 or roots[0].slot_id is not None or roots[0].item_id != self.weapon_item_id:
            raise ValueError('one root matching weapon_item_id is required')
        for node in self.nodes:
            if node.parent_node_id is not None and node.parent_node_id not in nodes:
                raise ValueError('unknown parent node')
        occupied = set()
        for node in self.nodes:
            if node.parent_node_id is not None:
                if node.parent_node_id not in nodes or node.slot_id is None:
                    raise ValueError('parent node and slot are required')
                key = (node.parent_node_id,node.slot_id)
                if key in occupied:
                    raise ValueError('one part per parent slot')
                occupied.add(key)
            visited = set()
            current = node
            while current.parent_node_id is not None:
                if current.node_id in visited:
                    raise ValueError('cyclic tree')
                visited.add(current.node_id)
                current = nodes[current.parent_node_id]
        return self


class CreateBuild(BuildContent):
    request_id: UUID


class UpdateBuild(BuildContent):
    expected_version: int = Field(ge=1)


class BuildVersion(BaseModel):
    expected_version: int = Field(ge=1)


class PublicationRevision(BaseModel):
    revision: int = Field(ge=1)


class CopyBuild(PublicationRevision):
    request_id: UUID


class CreateBuildComment(PublicationRevision):
    request_id: UUID
    content: str = Field(min_length=1, max_length=2000)

    @field_validator('content')
    @classmethod
    def clean_content(cls, value):
        value = value.strip()
        if not value:
            raise ValueError('content cannot be blank')
        return value


class UpdateBuildComment(BaseModel):
    expected_version: int = Field(ge=1)
    content: str = Field(min_length=1, max_length=2000)

    @field_validator('content')
    @classmethod
    def clean_content(cls, value):
        value = value.strip()
        if not value:
            raise ValueError('content cannot be blank')
        return value

# Response models keep the frontend contract visible in OpenAPI.
class StoredNode(BuildNodeInput):
    item: ItemSummary


class StoredContent(BaseModel):
    weapon_item_id: str
    title: str
    description: str
    nodes: list[StoredNode]


class BuildWarning(BaseModel):
    node_id: str
    code: Literal['SOURCE_ITEM_MISSING','SOURCE_SLOT_MISSING']


class CopySource(BaseModel):
    build_id: UUID | None
    revision: int
    title: str | None
    author_nickname: str | None


class Workspace(BaseModel):
    id: UUID
    version: int
    is_public: bool
    published_revision: int | None
    view: Literal['draft']
    content: StoredContent
    copied_from: CopySource | None
    created_at: datetime
    updated_at: datetime
    validation_scope: Literal['structure_only']
    warnings: list[BuildWarning]


class PublishedBuild(BaseModel):
    id: UUID
    revision: int
    is_public: bool
    is_mine: bool
    view: Literal['published']
    content: StoredContent
    author_nickname: str | None
    published_at: datetime
    copied_from: CopySource | None
    vote_count: int
    comment_count: int
    has_voted: bool
    validation_scope: Literal['structure_only']
    warnings: list[BuildWarning]


class PublicBuildSummary(BaseModel):
    id: UUID
    revision: int
    title: str
    weapon_item_id: str
    author_nickname: str | None
    published_at: datetime
    score: int
    vote_count: int
    comment_count: int
    weapon: ItemSummary


class PublicBuildPage(BaseModel):
    total: int
    page: int
    page_size: int
    sort: Literal['latest','best']
    period: Literal['week','month','all']
    builds: list[PublicBuildSummary]


class OwnBuildSummary(BaseModel):
    id: UUID
    title: str
    weapon_item_id: str
    version: int
    is_public: bool
    published_revision: int | None
    created_at: datetime
    updated_at: datetime


class OwnBuildPage(BaseModel):
    total: int
    page: int
    page_size: int
    builds: list[OwnBuildSummary]


class VoteResult(BaseModel):
    id: UUID
    revision: int
    has_voted: bool
    vote_count: int


class BuildComment(BaseModel):
    id: UUID
    content: str
    version: int
    created_at: datetime
    updated_at: datetime
    author_nickname: str | None
    is_mine: bool
    can_delete: bool


class BuildCommentPage(BaseModel):
    revision: int
    total: int
    page: int
    page_size: int
    comments: list[BuildComment]


class CreatedComment(BaseModel):
    id: UUID
    version: int
    revision: int


class UpdatedComment(BaseModel):
    id: UUID
    version: int


class DeletedResource(BaseModel):
    id: UUID
    deleted: Literal[True]


Result = TypeVar('Result')


class BuildResponse(BaseModel, Generic[Result]):
    status: Literal[200]
    msg: Literal['OK']
    data: Result


class BuildError(BaseModel):
    """Expected application/authentication errors; 422 uses HTTPValidationError."""
    detail: Literal[
        'LOGIN_REQUIRED', 'INVALID_TOKEN', 'AUTH_SERVICE_UNAVAILABLE',
        'BUILD_REGISTERED_USER_REQUIRED', 'BUILD_SELF_VOTE_FORBIDDEN',
        'BUILD_NOT_FOUND', 'BUILD_COMMENT_NOT_FOUND',
        'MODDING_WEAPON_NOT_FOUND', 'MODDING_ITEM_NOT_FOUND',
        'BUILD_VERSION_CONFLICT', 'BUILD_REVISION_CONFLICT', 'BUILD_REQUEST_CONFLICT',
        'BUILD_LIMIT_REACHED', 'BUILD_COMMENT_RATE_LIMITED', 'BUILD_STORAGE_UNAVAILABLE',
    ]

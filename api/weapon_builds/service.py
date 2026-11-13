"""User-authored build workspaces and immutable public revisions; no source writes."""
import hashlib
import json
from uuid import uuid4

from sqlalchemy import bindparam, text

from api.modding.service import ITEM_JSON, WEAPON_CONDITION
from util.http_exceptions import HttpError


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str, ensure_ascii=False).encode()).hexdigest()


def one(session, sql, params):
    row = session.execute(text(sql), params).mappings().one_or_none()
    return dict(row) if row is not None else None


def lock_actor(session, email):
    session.execute(text("select pg_advisory_xact_lock(hashtextextended(:key,0))"),
                    {'key':'weapon-build-user:'+email})


def get_build(session, build_id, lock=False):
    result = one(session,'select * from user_weapon_builds where id=:id'+(' for update' if lock else ''),{'id':build_id})
    if result is None:
        raise HttpError.BUILD_NOT_FOUND.exception()
    return result


def require_owner(build, actor):
    # Conceal private resources from other accounts.
    if actor is None or build['owner_email'] != actor['email']:
        raise HttpError.BUILD_NOT_FOUND.exception()


def expect_version(build, expected):
    if build['version'] != expected:
        raise HttpError.BUILD_VERSION_CONFLICT.exception()


def public_revision(session, build_id, revision=None, lock=False):
    build = get_build(session,build_id,lock)
    if not build['is_public']:
        raise HttpError.BUILD_NOT_FOUND.exception()
    if revision is not None and build['published_revision'] != revision:
        raise HttpError.BUILD_REVISION_CONFLICT.exception()
    return build


def provenance(build):
    if build['copied_from_revision'] is None:
        return None
    return {'build_id':build['copied_from_build_id'],'revision':build['copied_from_revision'],
            'title':build['source_title'],'author_nickname':build['source_author_nickname']}


def workspace(session, build):
    rows = session.execute(text('''select node_id,parent_node_id,slot_id,item_id,item_snapshot as item,
        attributes from user_weapon_build_nodes where build_id=:id order by sort_order'''),{'id':build['id']}).mappings()
    return {'weapon_item_id':build['weapon_item_id'],'title':build['title'],'description':build['description'],
            'nodes':[dict(row) for row in rows]}


def source_warnings(session, content):
    nodes=content['nodes']
    ids=list({n['item_id'] for n in nodes})
    statement=text('select id from items where id in :ids').bindparams(bindparam('ids',expanding=True))
    current=set(session.execute(statement,{'ids':ids}).scalars())
    statement=text('select item_id,slot_id from item_slots where item_id in :ids').bindparams(bindparam('ids',expanding=True))
    slots=set(tuple(r) for r in session.execute(statement,{'ids':ids}))
    parents={n['node_id']:n for n in nodes}
    warnings=[]
    for node in nodes:
        if node['item_id'] not in current:
            warnings.append({'node_id':node['node_id'],'code':'SOURCE_ITEM_MISSING'})
        if node['parent_node_id'] is not None:
            parent=parents[node['parent_node_id']]
            if (parent['item_id'],node['slot_id']) not in slots:
                warnings.append({'node_id':node['node_id'],'code':'SOURCE_SLOT_MISSING'})
    return warnings


def enrich_nodes(session, content, previous=None):
    ids=list({n['item_id'] for n in content['nodes']})
    query=text(f'select i.id,{ITEM_JSON} as item from items i where i.id in :ids').bindparams(bindparam('ids',expanding=True))
    current={r.id:r.item for r in session.execute(query,{'ids':ids})}
    previous_items={n['item_id']:n['item'] for n in (previous or {}).get('nodes',[])}
    root=content['weapon_item_id']
    valid_root=session.execute(text(f'select 1 from items i where i.id=:id and {WEAPON_CONDITION}'),{'id':root}).scalar_one_or_none()
    if valid_root is None and (previous is None or previous['weapon_item_id'] != root):
        raise HttpError.MODDING_WEAPON_NOT_FOUND.exception()
    nodes=[]
    for node in content['nodes']:
        item=current.get(node['item_id']) or previous_items.get(node['item_id'])
        if item is None:
            raise HttpError.MODDING_ITEM_NOT_FOUND.exception()
        nodes.append({**node,'item':item})
    return {**content,'nodes':nodes}


def write_nodes(session, build_id, nodes):
    session.execute(text('delete from user_weapon_build_nodes where build_id=:id'),{'id':build_id})
    session.execute(text('''insert into user_weapon_build_nodes
        (build_id,node_id,parent_node_id,slot_id,item_id,item_snapshot,attributes,sort_order)
        values (:id,:node_id,:parent_node_id,:slot_id,:item_id,cast(:snapshot as jsonb),cast(:attributes as jsonb),:sort)'''),
        [{'id':build_id,'node_id':n['node_id'],'parent_node_id':n['parent_node_id'],'slot_id':n['slot_id'],
          'item_id':n['item_id'],'snapshot':json.dumps(n['item'],default=str),'attributes':json.dumps(n['attributes']) if n['attributes'] is not None else None,'sort':i}
         for i,n in enumerate(nodes)])


def owner_result(session, build):
    content=workspace(session,build)
    return {'id':build['id'],'version':build['version'],'is_public':build['is_public'],
            'published_revision':build['published_revision'],'view':'draft','content':content,
            'copied_from':provenance(build),'created_at':build['created_at'],'updated_at':build['updated_at'],
            'validation_scope':'structure_only','warnings':source_warnings(session,content)}


def publication(session, build):
    return one(session,'''select snapshot,published_at from user_weapon_build_publications
        where build_id=:id and revision=:revision''',{'id':build['id'],'revision':build['published_revision']})


def public_result(session, build, actor):
    published=publication(session,build)
    if published is None:
        raise HttpError.BUILD_NOT_FOUND.exception()
    params={'id':build['id'],'revision':build['published_revision'],'email':actor['email'] if actor else None}
    counts=one(session,'''select
        (select count(*) from user_weapon_build_votes where build_id=:id and revision=:revision) as vote_count,
        (select count(*) from user_weapon_build_comments where build_id=:id and revision=:revision) as comment_count,
        exists(select 1 from user_weapon_build_votes where build_id=:id and revision=:revision and user_email=:email) as has_voted''',params)
    author=one(session,'select nickname from user_info where email=:email',{'email':build['owner_email']})
    return {'id':build['id'],'revision':build['published_revision'],'is_public':build['is_public'],
            'is_mine':actor is not None and actor['email']==build['owner_email'],
            'view':'published','content':published['snapshot'],'author_nickname':author['nickname'] if author else None,
            'published_at':published['published_at'],'copied_from':provenance(build),**counts,
            'validation_scope':'structure_only','warnings':source_warnings(session,published['snapshot'])}


class BuildService:
    @staticmethod
    def create(session, actor, request):
        content=request.model_dump(exclude={'request_id'},mode='json')
        signature=fingerprint({'operation':'create','content':content})
        lock_actor(session,actor['email'])
        existing=one(session,'select * from user_weapon_builds where owner_email=:email and request_id=:request',
                     {'email':actor['email'],'request':request.request_id})
        if existing:
            if existing['request_fingerprint'] != signature:
                raise HttpError.BUILD_REQUEST_CONFLICT.exception()
            return owner_result(session,existing)
        BuildService.quota(session,actor)
        content=enrich_nodes(session,content)
        build_id=uuid4()
        session.execute(text('''insert into user_weapon_builds
            (id,owner_email,request_id,request_fingerprint,weapon_item_id,title,description)
            values (:id,:email,:request,:signature,:weapon,:title,:description)'''),
            {'id':build_id,'email':actor['email'],'request':request.request_id,'signature':signature,
             'weapon':content['weapon_item_id'],'title':content['title'],'description':content['description']})
        write_nodes(session,build_id,content['nodes'])
        return owner_result(session,get_build(session,build_id))

    @staticmethod
    def quota(session, actor):
        count=session.execute(text('select count(*) from user_weapon_builds where owner_email=:email'),{'email':actor['email']}).scalar_one()
        if count >= 100:
            raise HttpError.BUILD_LIMIT_REACHED.exception()

    @staticmethod
    def update(session, actor, build_id, request):
        build=get_build(session,build_id,True);require_owner(build,actor);expect_version(build,request.expected_version)
        content=enrich_nodes(session,request.model_dump(exclude={'expected_version'},mode='json'),workspace(session,build))
        write_nodes(session,build_id,content['nodes'])
        session.execute(text('''update user_weapon_builds set weapon_item_id=:weapon,title=:title,description=:description,
            version=version+1,updated_at=now() where id=:id'''),
            {'weapon':content['weapon_item_id'],'title':content['title'],'description':content['description'],'id':build_id})
        return owner_result(session,get_build(session,build_id))

    @staticmethod
    def publish(session, actor, build_id, expected):
        build=get_build(session,build_id,True);require_owner(build,actor);expect_version(build,expected)
        if build['is_public'] and build['published_revision']==build['version']:
            return owner_result(session,build)
        content=workspace(session,build)
        revision=build['version']+1
        session.execute(text('''insert into user_weapon_build_publications(build_id,revision,snapshot)
            values (:id,:revision,cast(:snapshot as jsonb))'''),{'id':build_id,'revision':revision,'snapshot':json.dumps(content,default=str)})
        session.execute(text('''update user_weapon_builds set version=:revision,published_revision=:revision,
            is_public=true,updated_at=now() where id=:id'''),{'id':build_id,'revision':revision})
        return owner_result(session,get_build(session,build_id))

    @staticmethod
    def withdraw(session, actor, build_id, expected):
        build=get_build(session,build_id,True);require_owner(build,actor);expect_version(build,expected)
        session.execute(text('update user_weapon_builds set is_public=false,version=version+1,updated_at=now() where id=:id'),{'id':build_id})
        return owner_result(session,get_build(session,build_id))

    @staticmethod
    def delete(session, actor, build_id, expected):
        build=get_build(session,build_id,True);require_owner(build,actor);expect_version(build,expected)
        session.execute(text('delete from user_weapon_builds where id=:id'),{'id':build_id})
        return {'deleted':True,'id':build_id}

    @staticmethod
    def detail(session, actor, build_id, view):
        build=get_build(session,build_id)
        if view=='draft' or (not build['is_public'] and build['published_revision'] is None):
            require_owner(build,actor)
            return owner_result(session,build)
        if not build['is_public']:
            require_owner(build,actor)
        return public_result(session,build,actor)

    @staticmethod
    def mine(session, actor, page, page_size, word='', weapon_item_id=None):
        params={'email':actor['email'],'word':word.strip(),'weapon':weapon_item_id,
                'limit':page_size,'offset':(page-1)*page_size}
        source="""from user_weapon_builds where owner_email=:email
            and (:word='' or strpos(lower(title),lower(:word))>0)
            and (:weapon is null or weapon_item_id=:weapon)"""
        total=session.execute(text('select count(*) '+source),params).scalar_one()
        rows=session.execute(text('select id,title,weapon_item_id,version,is_public,published_revision, '
            'created_at,updated_at '+source+' order by updated_at desc,id limit :limit offset :offset'),params).mappings()
        return {'total':total,'page':page,'page_size':page_size,'builds':[dict(r) for r in rows]}

    @staticmethod
    def discover(session, weapon_id, word, sort, period, page, page_size):
        days={'week':7,'month':30,'all':None}[period]
        params={'weapon':weapon_id,'word':word.strip(),'days':days,'limit':page_size,'offset':(page-1)*page_size}
        # Public listing always uses snapshot metadata, never unpublished draft edits.
        source='''from user_weapon_builds b join user_weapon_build_publications p
            on p.build_id=b.id and p.revision=b.published_revision
            join user_info u on u.email=b.owner_email
            where b.is_public and (:weapon is null or p.snapshot->>'weapon_item_id'=:weapon)
            and (:word='' or strpos(lower(p.snapshot->>'title'),lower(:word))>0)'''
        total=session.execute(text('select count(*) '+source),params).scalar_one()
        score="""(select count(*) from user_weapon_build_votes v where v.build_id=b.id and v.revision=p.revision
            and (:days is null or v.created_at >= now()-cast(:days as integer)*interval '1 day'))"""
        order='score desc,p.published_at desc,b.id' if sort=='best' else 'p.published_at desc,b.id'
        rows=session.execute(text(f'''select b.id,p.revision,p.snapshot->>'title' as title,
            p.snapshot->>'weapon_item_id' as weapon_item_id,u.nickname as author_nickname,
            p.published_at,{score} as score,
            (select count(*) from user_weapon_build_votes v where v.build_id=b.id and v.revision=p.revision) as vote_count,
            (select count(*) from user_weapon_build_comments c where c.build_id=b.id and c.revision=p.revision) as comment_count,
            (select node->'item' from jsonb_array_elements(p.snapshot->'nodes') node where node->>'parent_node_id' is null limit 1) as weapon
            {source} order by {order} limit :limit offset :offset'''),params).mappings()
        return {'total':total,'page':page,'page_size':page_size,'sort':sort,'period':period,
                'builds':[dict(r) for r in rows]}

    @staticmethod
    def copy(session, actor, build_id, request):
        # Read lock order is consistent: account lock, then source build lock.
        lock_actor(session,actor['email'])
        signature=fingerprint({'operation':'copy','source':str(build_id),'revision':request.revision})
        existing=one(session,'select * from user_weapon_builds where owner_email=:email and request_id=:request',
                     {'email':actor['email'],'request':request.request_id})
        if existing:
            if existing['request_fingerprint']!=signature:
                raise HttpError.BUILD_REQUEST_CONFLICT.exception()
            return owner_result(session,existing)
        source=public_revision(session,build_id,request.revision,True)
        BuildService.quota(session,actor)
        content=publication(session,source)['snapshot']
        author=one(session,'select nickname from user_info where email=:email',{'email':source['owner_email']})
        target=uuid4()
        session.execute(text('''insert into user_weapon_builds
            (id,owner_email,request_id,request_fingerprint,weapon_item_id,title,description,
             copied_from_build_id,copied_from_revision,source_title,source_author_nickname)
            values (:id,:email,:request,:signature,:weapon,:title,:description,:source,:revision,:title,:nickname)'''),
            {'id':target,'email':actor['email'],'request':request.request_id,'signature':signature,
             'weapon':content['weapon_item_id'],'title':content['title'],'description':content['description'],
             'source':build_id,'revision':request.revision,'nickname':author['nickname'] if author else None})
        write_nodes(session,target,content['nodes'])
        return owner_result(session,get_build(session,target))

    @staticmethod
    def vote(session, actor, build_id, revision, enabled):
        build=public_revision(session,build_id,revision,True)
        if build['owner_email']==actor['email']:
            raise HttpError.BUILD_SELF_VOTE_FORBIDDEN.exception()
        params={'id':build_id,'revision':revision,'email':actor['email']}
        if enabled:
            session.execute(text('''insert into user_weapon_build_votes(build_id,revision,user_email)
                values (:id,:revision,:email) on conflict do nothing'''),params)
        else:
            session.execute(text('delete from user_weapon_build_votes where build_id=:id and revision=:revision and user_email=:email'),params)
        return {'id':build_id,'revision':revision,'has_voted':enabled,
                'vote_count':session.execute(text('select count(*) from user_weapon_build_votes where build_id=:id and revision=:revision'),params).scalar_one()}

    @staticmethod
    def comments(session, actor, build_id, page, page_size, revision=None):
        build=public_revision(session,build_id,revision)
        params={'id':build_id,'revision':build['published_revision'],'limit':page_size,'offset':(page-1)*page_size,
                'email':actor['email'] if actor else None,'admin':bool(actor and actor['is_admin'])}
        total=session.execute(text('select count(*) from user_weapon_build_comments where build_id=:id and revision=:revision'),params).scalar_one()
        rows=session.execute(text('''select c.id,c.content,c.version,c.created_at,c.updated_at,u.nickname as author_nickname,
            (c.author_email=:email) is true as is_mine,((c.author_email=:email) is true or :admin) as can_delete
            from user_weapon_build_comments c join user_info u on u.email=c.author_email
            where c.build_id=:id and c.revision=:revision order by c.created_at,c.id limit :limit offset :offset'''),params).mappings()
        return {'revision':build['published_revision'],'total':total,'page':page,'page_size':page_size,'comments':[dict(r) for r in rows]}

    @staticmethod
    def add_comment(session, actor, build_id, request):
        lock_actor(session,actor['email'])
        build=public_revision(session,build_id,request.revision,True)
        params={'email':actor['email'],'request':request.request_id}
        existing=one(session,'select * from user_weapon_build_comments where author_email=:email and request_id=:request',params)
        if existing:
            if existing['build_id']!=build_id or existing['revision']!=request.revision or existing['content']!=request.content:
                raise HttpError.BUILD_REQUEST_CONFLICT.exception()
            return {'id':existing['id'],'version':existing['version'],'revision':existing['revision']}
        recent=session.execute(text("select count(*) from user_weapon_build_comments where author_email=:email and created_at>now()-interval '60 seconds'"),params).scalar_one()
        if recent>=10:
            raise HttpError.BUILD_COMMENT_RATE_LIMITED.exception(headers={'Retry-After':'60'})
        comment_id=uuid4()
        session.execute(text('''insert into user_weapon_build_comments
            (id,build_id,revision,author_email,request_id,content) values (:id,:build,:revision,:email,:request,:content)'''),
            {**params,'id':comment_id,'build':build_id,'revision':request.revision,'content':request.content})
        return {'id':comment_id,'version':1,'revision':request.revision}

    @staticmethod
    def edit_comment(session, actor, build_id, comment_id, expected, content=None):
        # Build lock precedes comment lock, matching publication and comment creation.
        build=get_build(session,build_id,True)
        comment=one(session,'select * from user_weapon_build_comments where id=:id and build_id=:build for update',{'id':comment_id,'build':build_id})
        if comment is None or (comment['author_email']!=actor['email'] and not (content is None and actor['is_admin'])):
            raise HttpError.BUILD_COMMENT_NOT_FOUND.exception()
        if content is not None and (not build['is_public'] or build['published_revision']!=comment['revision']):
            raise HttpError.BUILD_REVISION_CONFLICT.exception()
        if comment['version']!=expected:
            raise HttpError.BUILD_VERSION_CONFLICT.exception()
        if content is None:
            session.execute(text('delete from user_weapon_build_comments where id=:id'),{'id':comment_id})
            return {'id':comment_id,'deleted':True}
        session.execute(text('update user_weapon_build_comments set content=:content,version=version+1,updated_at=now() where id=:id'),{'id':comment_id,'content':content})
        return {'id':comment_id,'version':expected+1}

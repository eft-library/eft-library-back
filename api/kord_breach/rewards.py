"""Manually curated season rewards. Quest start levels are never reward levels."""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel
from sqlalchemy import text
from util.http_exceptions import HttpError


class RewardItem(BaseModel):
    id: str
    name_en: str | None
    name_ko: str | None
    name_ja: str | None
    image: str | None
    normalized_name: str | None
    category: str | None


class RewardQuest(BaseModel):
    id: str
    name_en: str | None
    name_ko: str | None
    name_ja: str | None
    normalized_name: str | None
    start_required_level: int | None
    is_registered: bool


class RewardCondition(BaseModel):
    group_no: int
    sort_order: int
    condition_type: Literal['player_level', 'quest_completed']
    required_level: int | None
    quest: RewardQuest | None


class SeasonReward(BaseModel):
    id: str
    sort_order: int
    item: RewardItem
    required_level: int | None
    unlock_conditions_known: bool
    unlock_conditions: list[RewardCondition]


class RewardsResult(BaseModel):
    season_id: str
    total: int
    source_url: str
    source_revision: str
    collected_at: datetime
    condition_logic: Literal['or_groups_of_and_conditions']
    rewards: list[SeasonReward]


def get_rewards(session, season_id):
    snapshot = session.execute(text('select * from kord_breach_reward_snapshots where season_id=:season'), {'season':season_id}).mappings().one_or_none()
    if snapshot is None:
        raise HttpError.KORD_REWARDS_UNAVAILABLE.exception()
    rows = session.execute(text('''select r.id, r.sort_order, r.unlock_conditions_known,
        jsonb_build_object('id',i.id,'name_en',i.name_en,'name_ko',i.name_ko,'name_ja',i.name_ja,
        'image',i.image,'normalized_name',i.normalized_name,'category',i.category) as item
        from kord_breach_rewards r join items i on i.id=r.item_id
        where r.season_id=:season order by r.sort_order,r.id'''), {'season':season_id}).mappings().all()
    conditions = session.execute(text('''select c.*, q.id as registered_quest_id, q.name_en,q.name_ko,q.name_ja,
        q.normalized_name,q.min_player_level from kord_breach_reward_conditions c
        left join quests q on q.id=c.quest_id where c.season_id=:season
        order by c.reward_id,c.group_no,c.sort_order'''), {'season':season_id}).mappings().all()
    indexed = {}
    for row in conditions:
        quest = None if row['quest_id'] is None else {
            'id':row['quest_id'], **{k:row[k] for k in ('name_en','name_ko','name_ja','normalized_name')},
            'start_required_level':row['min_player_level'], 'is_registered':row['registered_quest_id'] is not None}
        indexed.setdefault(row['reward_id'], []).append({k:row[k] for k in ('group_no','sort_order','condition_type','required_level')} | {'quest':quest})
    rewards = []
    for row in rows:
        cs = indexed.get(row['id'], [])
        # Only a single direct level condition can safely be summarized by one number.
        level = cs[0]['required_level'] if row['unlock_conditions_known'] and len(cs)==1 and cs[0]['condition_type']=='player_level' else None
        rewards.append(dict(row) | {'required_level':level, 'unlock_conditions':cs})
    return dict(snapshot) | {'total':len(rewards), 'rewards':rewards, 'condition_logic':'or_groups_of_and_conditions'}

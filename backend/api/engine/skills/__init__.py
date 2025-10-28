"""
Clause-specific skills for proposal generation
"""
from .base_skill import BaseSkill
from .exclusivity_skill import ExclusivitySkill
from .preemption_skill import PreemptionSkill
from .vesting_skill import VestingSkill
from .transfer_skill import TransferSkill

__all__ = [
    'BaseSkill',
    'ExclusivitySkill',
    'PreemptionSkill',
    'VestingSkill',
    'TransferSkill'
]



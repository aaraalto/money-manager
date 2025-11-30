from typing import Dict, List
from app.models import Liability, LiabilityTag

def group_liabilities_by_tag(liabilities: List[Liability]) -> Dict[LiabilityTag, List[Liability]]:
    """
    Groups a list of liabilities by their tags.
    Since a liability can have multiple tags, it may appear in multiple groups.
    """
    grouped: Dict[LiabilityTag, List[Liability]] = {tag: [] for tag in LiabilityTag}
    
    for liability in liabilities:
        for tag in liability.tags:
            if tag in grouped:
                grouped[tag].append(liability)
                
    return grouped

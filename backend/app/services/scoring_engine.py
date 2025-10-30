"""
Scoring Engine

Converts canonical events into score deltas based on game rules.
This is where your game mechanics live!
"""
from typing import List
from uuid import UUID
import math

from app.schemas.scoring import ScoreDelta, DeltaType
from app.services.event_normalizer import CanonicalEvent, EventType


class ScoringEngine:
    """
    Applies scoring rules to events.
    
    Philosophy:
    - Keep rules simple initially
    - Make them data-driven (could come from database later)
    - One event can produce multiple deltas (e.g., PR merge gives food AND happiness)
    
    Reward Configuration:
    Adjust these constants to tune your game economy!
    """
    # === REWARD CONSTANTS - ADJUST THESE VALUES ===
    COMMIT_FOOD = 1.0              # Food per commit
    PR_OPENED_FOOD = 3.0           # Food for opening a PR
    PR_MERGED_FOOD = 5.0           # Food for merging a PR
    PR_MERGED_HAPPINESS = 3.0      # Happiness bonus for PR merge
    COMMIT_COMMENT_FOOD = 0.5      # Food for commit comments
    
    STRAVA_ACTIVITY_FOOD = 2.0        # Base food for any activity
    STRAVA_ACTIVITY_HAPPINESS = 1.0   # Happiness from exercise
    # ==============================================
    
    def score_event(self, event: CanonicalEvent, pet_id: UUID) -> List[ScoreDelta]:
        """
        Apply scoring rules to an event.
        
        Args:
            event: The canonical event to score
            pet_id: Which pet to credit
            
        Returns:
            List of ScoreDeltas (can be empty, or multiple)
            
        Example:
            A GitHub commit might return:
            [ScoreDelta(delta_type="energy", amount=1.0, ...)]
            
            A PR merge might return:
            [
                ScoreDelta(delta_type="energy", amount=5.0, ...),
                ScoreDelta(delta_type="happiness", amount=2.0, ...)
            ]
        """
        # Route to appropriate scoring rule
        if event.type == EventType.GITHUB_COMMIT:
            return self._score_github_commit(event, pet_id)
        
        elif event.type == EventType.GITHUB_PR_OPENED:
            return self._score_github_pr_opened(event, pet_id)
        
        elif event.type == EventType.GITHUB_PR_MERGED:
            return self._score_github_pr_merged(event, pet_id)
        
        elif event.type == EventType.MANUAL_HABIT:
            return self._score_manual_habit(event, pet_id)
        
        elif event.type == EventType.STRAVA_ACTIVITY:
            return self._score_strava_activity(event, pet_id)
        
        # Unknown event type - no scoring
        return []
    
    def _score_github_commit(self, event: CanonicalEvent, pet_id: UUID) -> List[ScoreDelta]:
        """
        Score a GitHub commit.
        
        Rule: 1 commit = 1 food point
        Food is stored and consumed by the pet. Excess converts to currency.
        
        Future ideas:
        - Weekend commits = 2x points (motivate weekend coding)
        - Large commits (100+ lines) = bonus
        - Commits to main branch = more valuable
        - Morning commits (before 9am) = early bird bonus
        """
        # Use configured reward value
        food_gain = self.COMMIT_FOOD
        
        return [
            ScoreDelta(
                delta_type=DeltaType.FOOD,
                amount=food_gain,
                event_id=event.event_raw_id,
                pet_id=pet_id,
                timestamp=event.timestamp,
                meta={
                    'event_type': event.type,
                    'repository': event.meta.get('repository'),
                    'branch': event.meta.get('branch')
                }
            )
        ]
    
    def _score_github_pr_opened(self, event: CanonicalEvent, pet_id: UUID) -> List[ScoreDelta]:
        """
        Score opening a pull request.
        
        Opening a PR shows proactive collaboration!
        PRs give more food than single commits.
        """
        return [
            ScoreDelta(
                delta_type=DeltaType.FOOD,
                amount=self.PR_OPENED_FOOD,
                event_id=event.event_raw_id,
                pet_id=pet_id,
                timestamp=event.timestamp,
                meta={'event_type': event.type}
            )
        ]
    
    def _score_github_pr_merged(self, event: CanonicalEvent, pet_id: UUID) -> List[ScoreDelta]:
        """
        Score merging a pull request.
        
        Merged PR = completed work! Give food AND happiness.
        This is a big accomplishment, so reward generously.
        """
        return [
            ScoreDelta(
                delta_type=DeltaType.FOOD,
                amount=self.PR_MERGED_FOOD,
                event_id=event.event_raw_id,
                pet_id=pet_id,
                timestamp=event.timestamp,
                meta={'event_type': event.type}
            ),
            ScoreDelta(
                delta_type=DeltaType.HAPPINESS,
                amount=self.PR_MERGED_HAPPINESS,
                event_id=event.event_raw_id,
                pet_id=pet_id,
                timestamp=event.timestamp,
                meta={'event_type': event.type}
            )
        ]
    
    def _score_manual_habit(self, event: CanonicalEvent, pet_id: UUID) -> List[ScoreDelta]:
        """
        Score a manually-tracked habit.
        
        Use the event.value directly - user can set custom point values.
        Converts user's effort into food for their pet.
        """
        return [
            ScoreDelta(
                delta_type=DeltaType.FOOD,
                amount=event.value,
                event_id=event.event_raw_id,
                pet_id=pet_id,
                timestamp=event.timestamp,
                meta={
                    'event_type': event.type,
                    'title': event.meta.get('title')
                }
            )
        ]
    
    def _score_strava_activity(self, event: CanonicalEvent, pet_id: UUID) -> List[ScoreDelta]:
        """
        Score a Strava activity.
        
        Rule: Base food + distance/duration bonuses (calculated in normalizer)
        Also gives happiness because exercise feels good!
        
        Future ideas:
        - PR (personal record) bonus
        - Kudos multiplier
        - Streak bonuses
        - Different rewards for run vs ride vs swim
        """
        # Use the value calculated in normalizer (includes distance/duration bonuses)
        food_amount = event.value * self.STRAVA_ACTIVITY_FOOD
        
        return [
            ScoreDelta(
                delta_type=DeltaType.FOOD,
                amount=food_amount,
                event_id=event.event_raw_id,
                pet_id=pet_id,
                timestamp=event.timestamp,
                meta={
                    'event_type': event.type,
                    'activity_type': event.meta.get('activity_type'),
                    'distance_km': event.meta.get('distance_km')
                }
            ),
            ScoreDelta(
                delta_type=DeltaType.HAPPINESS,
                amount=self.STRAVA_ACTIVITY_HAPPINESS,
                event_id=event.event_raw_id,
                pet_id=pet_id,
                timestamp=event.timestamp,
                meta={'event_type': event.type}
            )
        ]

// Goal type definitions matching backend schema

export type GoalType = 'long_term' | 'short_term';
export type TrackingType = 'binary' | 'numeric';
export type IntegrationSource = 'github' | 'strava' | 'manual';
export type GrowthStage = 0 | 1 | 2 | 3;

export interface GoalState {
  // Tracking data
  daily_progress: Record<string, number>;
  weekly_totals: Record<string, number>;
  monthly_totals: Record<string, number>;
  streak_data: {
    current_streak: number;
    longest_streak: number;
    last_completed_date?: string;
  };
  
  // Metadata
  notes?: string;
  tags?: string[];
  custom_fields?: Record<string, any>;
}

export interface Goal {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  goal_type: GoalType;
  integration_source: IntegrationSource;
  integration_id?: string;
  tracking_type: TrackingType;
  target_value: number;
  unit?: string;
  visual_variant?: string;
  deadline?: string;
  current_progress: number;
  is_completed: boolean;
  is_crowned: boolean;
  completed_at?: string;
  last_completed_date?: string;
  total_medallions_produced: number;
  growth_stage: GrowthStage;
  state_json: GoalState;
  created_at: string;
  updated_at: string;
}

export interface GoalCreate {
  name: string;
  description?: string;
  goal_type: GoalType;
  integration_source?: IntegrationSource;
  integration_id?: string;
  tracking_type?: TrackingType;
  target_value: number;
  unit?: string;
  visual_variant?: string;
  deadline?: string;
}

export interface GoalUpdate {
  name?: string;
  description?: string;
  target_value?: number;
  unit?: string;
  visual_variant?: string;
  deadline?: string;
  is_completed?: boolean;
}

export interface GoalStats {
  total_goals: number;
  active_goals: number;
  completed_goals: number;
  crowned_goals: number;
  total_medallions_earned: number;
  average_completion_rate: number;
  longest_streak: number;
  current_streak: number;
}

export interface GoalTemplate {
  id: string;
  name: string;
  description: string;
  goal_type: GoalType;
  integration_source: IntegrationSource;
  tracking_type: TrackingType;
  target_value: number;
  unit: string;
  visual_variant: string;
  category: string;
}

export interface GoalTemplateResponse {
  templates: GoalTemplate[];
  count: number;
}

export interface CreateGoalFromTemplate {
  template_id: string;
  name?: string;
  target_value?: number;
}

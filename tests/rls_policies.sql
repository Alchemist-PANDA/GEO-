-- Run this in Supabase -> SQL Editor, after your existing supabase_schema.sql.
-- 1. Turn on Row Level Security for every table that holds real data.
alter table public.user_profiles enable row level security;
alter table public.brands enable row level security;
alter table public.audits enable row level security;
alter table public.audit_feedback enable row level security;
alter table public.llm_call_logs enable row level security;
alter table public.guardrail_events enable row level security;
alter table public.competitors enable row level security;
alter table public.competitor_scans enable row level security;
alter table public.competitor_scores enable row level security;
alter table public.competitor_explanations enable row level security;
alter table public.alerts enable row level security;
alter table public.competitor_feedback enable row level security;
alter table public.copilot_conversations enable row level security;
alter table public.copilot_messages enable row level security;
alter table public.action_plans enable row level security;
alter table public.action_executions enable row level security;
alter table public.billing_history enable row level security;
alter table public.audit_usage enable row level security;
alter table public.invoice_requests enable row level security;

-- 2. Define Policies
-- user_profiles
create policy "users can read own profile" on public.user_profiles for select to authenticated using (auth.uid() = id);
create policy "users can insert own profile" on public.user_profiles for insert to authenticated with check (auth.uid() = id);
create policy "users can update own profile" on public.user_profiles for update to authenticated using (auth.uid() = id);

-- brands
create policy "users can read own brands" on public.brands for select to authenticated using (auth.uid() = user_id);
create policy "users can insert own brands" on public.brands for insert to authenticated with check (auth.uid() = user_id);
create policy "users can update own brands" on public.brands for update to authenticated using (auth.uid() = user_id);
create policy "users can delete own brands" on public.brands for delete to authenticated using (auth.uid() = user_id);

-- audits
create policy "users can read own audits" on public.audits for select to authenticated using (
    exists (select 1 from brands where brands.id = audits.brand_id and brands.user_id = auth.uid())
);
create policy "users can insert own audits" on public.audits for insert to authenticated with check (
    exists (select 1 from brands where brands.id = audits.brand_id and brands.user_id = auth.uid())
);
create policy "users can update own audits" on public.audits for update to authenticated using (
    exists (select 1 from brands where brands.id = audits.brand_id and brands.user_id = auth.uid())
);
create policy "users can delete own audits" on public.audits for delete to authenticated using (
    exists (select 1 from brands where brands.id = audits.brand_id and brands.user_id = auth.uid())
);

-- audit_feedback
create policy "users can read own audit_feedback" on public.audit_feedback for select to authenticated using (auth.uid() = user_id);
create policy "users can insert own audit_feedback" on public.audit_feedback for insert to authenticated with check (auth.uid() = user_id);
create policy "users can update own audit_feedback" on public.audit_feedback for update to authenticated using (auth.uid() = user_id);
create policy "users can delete own audit_feedback" on public.audit_feedback for delete to authenticated using (auth.uid() = user_id);

-- llm_call_logs
create policy "users can read own llm_call_logs" on public.llm_call_logs for select to authenticated using (auth.uid() = user_id);
create policy "users can insert own llm_call_logs" on public.llm_call_logs for insert to authenticated with check (auth.uid() = user_id);

-- guardrail_events
create policy "users can read own guardrail_events" on public.guardrail_events for select to authenticated using (auth.uid() = user_id);
create policy "users can insert own guardrail_events" on public.guardrail_events for insert to authenticated with check (auth.uid() = user_id);

-- competitors
create policy "users can read own competitors" on public.competitors for select to authenticated using (
    exists (select 1 from brands where brands.id = competitors.brand_id and brands.user_id = auth.uid())
);
create policy "users can insert own competitors" on public.competitors for insert to authenticated with check (
    exists (select 1 from brands where brands.id = competitors.brand_id and brands.user_id = auth.uid())
);
create policy "users can update own competitors" on public.competitors for update to authenticated using (
    exists (select 1 from brands where brands.id = competitors.brand_id and brands.user_id = auth.uid())
);
create policy "users can delete own competitors" on public.competitors for delete to authenticated using (
    exists (select 1 from brands where brands.id = competitors.brand_id and brands.user_id = auth.uid())
);

-- competitor_scans
create policy "users can read own competitor_scans" on public.competitor_scans for select to authenticated using (
    exists (select 1 from competitors join brands on competitors.brand_id = brands.id where competitors.id = competitor_scans.competitor_id and brands.user_id = auth.uid())
);
create policy "users can insert own competitor_scans" on public.competitor_scans for insert to authenticated with check (
    exists (select 1 from competitors join brands on competitors.brand_id = brands.id where competitors.id = competitor_scans.competitor_id and brands.user_id = auth.uid())
);
create policy "users can update own competitor_scans" on public.competitor_scans for update to authenticated using (
    exists (select 1 from competitors join brands on competitors.brand_id = brands.id where competitors.id = competitor_scans.competitor_id and brands.user_id = auth.uid())
);

-- competitor_scores
create policy "users can read own competitor_scores" on public.competitor_scores for select to authenticated using (
    exists (select 1 from competitors join brands on competitors.brand_id = brands.id where competitors.id = competitor_scores.competitor_id and brands.user_id = auth.uid())
);
create policy "users can insert own competitor_scores" on public.competitor_scores for insert to authenticated with check (
    exists (select 1 from competitors join brands on competitors.brand_id = brands.id where competitors.id = competitor_scores.competitor_id and brands.user_id = auth.uid())
);

-- competitor_explanations
create policy "users can read own competitor_explanations" on public.competitor_explanations for select to authenticated using (
    exists (select 1 from competitors join brands on competitors.brand_id = brands.id where competitors.id = competitor_explanations.competitor_id and brands.user_id = auth.uid())
);
create policy "users can insert own competitor_explanations" on public.competitor_explanations for insert to authenticated with check (
    exists (select 1 from competitors join brands on competitors.brand_id = brands.id where competitors.id = competitor_explanations.competitor_id and brands.user_id = auth.uid())
);

-- alerts
create policy "users can read own alerts" on public.alerts for select to authenticated using (auth.uid() = user_id);
create policy "users can insert own alerts" on public.alerts for insert to authenticated with check (auth.uid() = user_id);
create policy "users can update own alerts" on public.alerts for update to authenticated using (auth.uid() = user_id);
create policy "users can delete own alerts" on public.alerts for delete to authenticated using (auth.uid() = user_id);

-- competitor_feedback
create policy "users can read own competitor_feedback" on public.competitor_feedback for select to authenticated using (auth.uid() = user_id);
create policy "users can insert own competitor_feedback" on public.competitor_feedback for insert to authenticated with check (auth.uid() = user_id);
create policy "users can update own competitor_feedback" on public.competitor_feedback for update to authenticated using (auth.uid() = user_id);
create policy "users can delete own competitor_feedback" on public.competitor_feedback for delete to authenticated using (auth.uid() = user_id);

-- copilot_conversations
create policy "users can read own copilot_conversations" on public.copilot_conversations for select to authenticated using (auth.uid() = user_id);
create policy "users can insert own copilot_conversations" on public.copilot_conversations for insert to authenticated with check (auth.uid() = user_id);
create policy "users can update own copilot_conversations" on public.copilot_conversations for update to authenticated using (auth.uid() = user_id);
create policy "users can delete own copilot_conversations" on public.copilot_conversations for delete to authenticated using (auth.uid() = user_id);

-- copilot_messages
create policy "users can read own copilot_messages" on public.copilot_messages for select to authenticated using (
    exists (select 1 from copilot_conversations where copilot_conversations.id = copilot_messages.conversation_id and copilot_conversations.user_id = auth.uid())
);
create policy "users can insert own copilot_messages" on public.copilot_messages for insert to authenticated with check (
    exists (select 1 from copilot_conversations where copilot_conversations.id = copilot_messages.conversation_id and copilot_conversations.user_id = auth.uid())
);

-- action_plans
create policy "users can read own action_plans" on public.action_plans for select to authenticated using (
    exists (select 1 from brands where brands.id = action_plans.brand_id and brands.user_id = auth.uid())
);
create policy "users can insert own action_plans" on public.action_plans for insert to authenticated with check (
    exists (select 1 from brands where brands.id = action_plans.brand_id and brands.user_id = auth.uid())
);
create policy "users can update own action_plans" on public.action_plans for update to authenticated using (
    exists (select 1 from brands where brands.id = action_plans.brand_id and brands.user_id = auth.uid())
);

-- action_executions
create policy "users can read own action_executions" on public.action_executions for select to authenticated using (
    exists (select 1 from action_plans join brands on action_plans.brand_id = brands.id where action_plans.id = action_executions.plan_id and brands.user_id = auth.uid())
);
create policy "users can insert own action_executions" on public.action_executions for insert to authenticated with check (
    exists (select 1 from action_plans join brands on action_plans.brand_id = brands.id where action_plans.id = action_executions.plan_id and brands.user_id = auth.uid())
);
create policy "users can update own action_executions" on public.action_executions for update to authenticated using (
    exists (select 1 from action_plans join brands on action_plans.brand_id = brands.id where action_plans.id = action_executions.plan_id and brands.user_id = auth.uid())
);

-- billing_history
create policy "users can read own billing_history" on public.billing_history for select to authenticated using (auth.uid() = user_id);
create policy "users can insert own billing_history" on public.billing_history for insert to authenticated with check (auth.uid() = user_id);

-- audit_usage
create policy "users can read own audit_usage" on public.audit_usage for select to authenticated using (auth.uid() = user_id);
create policy "users can insert own audit_usage" on public.audit_usage for insert to authenticated with check (auth.uid() = user_id);
create policy "users can update own audit_usage" on public.audit_usage for update to authenticated using (auth.uid() = user_id);

-- invoice_requests
create policy "users can read own invoice_requests" on public.invoice_requests for select to authenticated using (auth.uid() = user_id);
create policy "users can insert own invoice_requests" on public.invoice_requests for insert to authenticated with check (auth.uid() = user_id);
create policy "users can update own invoice_requests" on public.invoice_requests for update to authenticated using (auth.uid() = user_id);

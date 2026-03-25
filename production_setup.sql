-- ==========================================
-- LABOR GROW: PRODUCTION BACKEND SQL SCRIPT
-- ==========================================
-- This script sets up the chat system and 
-- automated 24-hour message cleanup.

-- 1. Create chat_messages table
CREATE TABLE IF NOT EXISTS public.chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sender_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    receiver_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Enable Row Level Security (RLS)
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;

-- 3. Security Policies
-- Allow users to see messages they sent or received
CREATE POLICY "Users can view own chat messages" ON public.chat_messages
    FOR SELECT USING (auth.uid() = sender_id OR auth.uid() = receiver_id);

-- Allow users to send messages (as themselves)
CREATE POLICY "Users can insert own chat messages" ON public.chat_messages
    FOR INSERT WITH CHECK (auth.uid() = sender_id);

-- Allow marking messages as read
CREATE POLICY "Users can update own chat messages" ON public.chat_messages
    FOR UPDATE USING (auth.uid() = receiver_id);

-- 4. 24-Hour Automated Cleanup (Requires pg_cron)
-- If your Supabase instance has pg_cron enabled, run this:
-- SELECT cron.schedule('0 * * * *', $$DELETE FROM chat_messages WHERE created_at < NOW() - INTERVAL '24 hours'$$);

-- Alternative: If you don't have pg_cron, you can use a manual cleanup function
-- that you periodically call from your API:
/*
CREATE OR REPLACE FUNCTION delete_old_messages() RETURNS void AS $$
BEGIN
    DELETE FROM public.chat_messages WHERE created_at < NOW() - INTERVAL '24 hours';
END;
$$ LANGUAGE plpgsql;
*/

-- 5. Notifications table (Ensure it exists)
CREATE TABLE IF NOT EXISTS public.notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    type TEXT DEFAULT 'general',
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own notifications" ON public.notifications
    FOR SELECT USING (auth.uid() = user_id);

SELECT 
    w.id AS workout_id,
    w.actual_date, 
    e.name_ua AS exercise_name, 
    f.number_approaches, 
    f.repeat_exercise, 
    COALESCE(wt.tools, 'Власна вага') AS weight_tool,
    wt.weight_value
FROM public.workout w
 LEFT JOIN public.workout_fact f ON f.workout_id = w.id
 LEFT JOIN public.exercise e ON f.exercise_id = e.id
 LEFT JOIN public.weight wt ON f.weight_id = wt.id
WHERE w.actual_date::date = '2026-06-20'
ORDER BY w.actual_date DESC; 
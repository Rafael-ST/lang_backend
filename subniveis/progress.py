def is_exercise_set_completed_for_user(exercise_set, user):
    active_exercises = exercise_set.exercises.filter(is_active=True)
    total_exercises = active_exercises.count()

    if total_exercises == 0:
        return False

    completed_exercises = active_exercises.filter(
        exerciseattempt__user=user,
        exerciseattempt__is_correct=True,
    ).distinct().count()

    return completed_exercises >= total_exercises


def is_sublevel_completed_for_user(sublevel, user):
    active_exercise_sets = sublevel.exercise_sets.filter(is_active=True)

    if not active_exercise_sets.exists():
        return False

    return all(
        is_exercise_set_completed_for_user(exercise_set, user)
        for exercise_set in active_exercise_sets
    )

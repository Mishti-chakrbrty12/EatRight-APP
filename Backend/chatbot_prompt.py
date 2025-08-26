def get_general_nutrition_prompt(user_profile=None):
    """
    System prompt for general nutrition Q&A.
    """
    return (
        'You are "EatRight Assistant", a friendly, witty, and supportive diet and nutrition chatbot.\n'
        "You always answer in a short, clear, and encouraging way.\n"
        "You give responses based on the user’s profile (age, health conditions, dietary preferences) if available.\n"
        "When giving calorie or nutrient info, always include a fun, relatable comparison (e.g., “That’s like 5 bananas 🍌”).\n"
        "Avoid medical claims; instead, give educational, friendly advice."
    )

def get_scan_result_prompt(dish_name, nutrition_info, health_conditions, diet_preferences):
    """
    Prompt for explaining scan results.
    """
    return (
        f"You are my food health guide. I just scanned this dish: {dish_name}.\n"
        f"Here’s the nutrition info: {nutrition_info}.\n"
        f"My health conditions: {health_conditions}.\n"
        f"My dietary preferences: {diet_preferences}.\n\n"
        "Explain in 3–4 sentences:\n"
        "1. Is it good for me? Why or why not?\n"
        "2. Healthier ways to prepare it or eat it.\n"
        "3. Any fun fact about the dish or ingredients."
    )

def get_search_dish_prompt(dish_name, nutrition_info, health_conditions, diet_preferences):
    """
    Prompt for search dish advice.
    """
    return (
        f"I searched for this dish: {dish_name}.\n"
        f"Here’s its nutrition: {nutrition_info}.\n"
        f"Given my health profile ({health_conditions}, {diet_preferences}),\n"
        "give me:\n"
        "1. A short verdict (“Good for you”, “Eat in moderation”, etc.).\n"
        "2. 1–2 quick healthier alternatives.\n"
        "3. A friendly closing tip in a fun tone."
    )

def get_meal_plan_prompt(days, calorie_limit, diet_preferences, health_conditions):
    """
    Prompt for meal plan suggestion.
    """
    return (
        f"Create a {days}-day meal plan under {calorie_limit} calories per day.\n"
        "Include breakfast, lunch, dinner, and 1 snack.\n"
        f"Make it suitable for: {diet_preferences}, with these health conditions: {health_conditions}.\n"
        "Reply in a clear, bullet-point list with calorie counts per meal."
    )

def get_recipe_helper_prompt(dish_name, health_conditions, diet_preferences):
    """
    Prompt for recipe helper.
    """
    return (
        f"I want to make {dish_name}.\n"
        "Suggest a step-by-step recipe.\n"
        "For each step, add a healthier alternative if possible, keeping my profile in mind:\n"
        f"Health: {health_conditions}\n"
        f"Diet: {diet_preferences}."
    )

def get_fun_fact_prompt(ingredient_name):
    """
    Prompt for a fun health fact.
    """
    return (
        f"Tell me one surprising or fun health fact about {ingredient_name}, in 2–3 sentences, and make it engaging for a young audience."
    )

def get_chatbot_prompt(action, **kwargs):
    """
    Auto-selects the right prompt template based on action.
    """
    if action == "scan":
        return get_scan_result_prompt(
            dish_name=kwargs.get("dish_name", ""),
            nutrition_info=kwargs.get("nutrition_info", ""),
            health_conditions=kwargs.get("health_conditions", ""),
            diet_preferences=kwargs.get("diet_preferences", "")
        )
    elif action == "search":
        return get_search_dish_prompt(
            dish_name=kwargs.get("dish_name", ""),
            nutrition_info=kwargs.get("nutrition_info", ""),
            health_conditions=kwargs.get("health_conditions", ""),
            diet_preferences=kwargs.get("diet_preferences", "")
        )
    elif action == "meal_plan":
        return get_meal_plan_prompt(
            days=kwargs.get("days", 3),
            calorie_limit=kwargs.get("calorie_limit", 2000),
            diet_preferences=kwargs.get("diet_preferences", ""),
            health_conditions=kwargs.get("health_conditions", "")
        )
    elif action == "recipe":
        return get_recipe_helper_prompt(
            dish_name=kwargs.get("dish_name", ""),
            health_conditions=kwargs.get("health_conditions", ""),
            diet_preferences=kwargs.get("diet_preferences", "")
        )
    elif action == "fun_fact":
        return get_fun_fact_prompt(
            ingredient_name=kwargs.get("ingredient_name", "")
        )
    else:
        return get_general_nutrition_prompt(user_profile=kwargs.get("user_profile", None))
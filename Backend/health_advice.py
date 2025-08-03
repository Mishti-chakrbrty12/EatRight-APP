def get_health_verdict(dish_name: str, nutrition: dict):
    verdict = {}

    fats = float(nutrition.get("Fats", 0))
    sodium = float(nutrition.get("Sodium", 0))
    calories = float(nutrition.get("Calories", 0))

    dish_lower = dish_name.lower()

    if "biryani" in dish_lower or fats > 12 or sodium > 500:
        verdict["warning"] = "⚠️ High cholesterol: Avoid biryanis or oily dishes"
        verdict["suggested"] = "✅ Suggested Alternative: Grilled chicken with steamed rice"
    else:
        verdict["warning"] = "👍 This dish seems okay in moderation."
        verdict["suggested"] = "Try grilled or steamed versions for best health."

    return verdict

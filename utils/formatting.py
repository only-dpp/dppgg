import discord
def rank_color(rank_name):
    if not rank_name:
        return discord.Color.default()

    rank_name = rank_name.lower()
    color_map = {
        "challenger": discord.Color.from_rgb(85, 170, 255),
        "grandmaster": discord.Color.from_rgb(200, 20, 20),
        "master": discord.Color.purple(),
        "diamond": discord.Color.from_rgb(115, 255, 255),
        "platinum": discord.Color.from_rgb(25, 220, 160),
        "gold": discord.Color.gold(),
        "silver": discord.Color.light_grey(),
        "bronze": discord.Color.from_rgb(120, 72, 36),
        "iron": discord.Color.darker_grey(),
    }

    for key, color in color_map.items():
        if key in rank_name:
            return color

    return discord.Color.default()

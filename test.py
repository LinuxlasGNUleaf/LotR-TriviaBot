import lotr_config
list_ = lotr_config.DISCORD_CONFIG['hangman.ongoing_states']
list_.append(lotr_config.DISCORD_CONFIG['hangman.won_state'])
list_.append(lotr_config.DISCORD_CONFIG['hangman.lost_state'])
for i,item in enumerate(list_):
    print(i, "\n", item.replace("```", ""))
    print("\n\n")
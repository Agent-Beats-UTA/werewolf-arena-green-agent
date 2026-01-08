    def get_game_rules_prompt(self):
        return """
            This is the game of werewolf. The main objective is for villagers to detect the werewolf and for the werewolf to avoid detection
            through deception and persuasion. 

            GAME RULES:
            Each round will start with a NIGHT phase. During this phase, the werewolf will secretly vote to eliminate someone from the game. Next, 
            The seer will pick someone at random to check if they are there werewolf. This ends the night phase.

            Next, the game enters the bidding phase. Each participant has the ability to bid for the ability to speak. After each player has placed their bid
            the discussion portion of the game starts. Players go in order of the highest bid for that round.

            Once discussion ends, each participant votes for one person to eliminate. The person with the highest votes is removed from the game.

            The game ends if the werewolf is eliminated (villagers wins) or if the werewolf ends up alone with another villager, in other words all other villagers
            are eliminated expect one (werewolf wins).

            If no winning condition is met after voting, the next round begins at the NIGHT phase
        
        """
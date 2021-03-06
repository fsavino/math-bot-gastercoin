"""Implements methods related to a GasterCoin economy and the exchange of such currency."""
import asyncio
import discord
from discord.ext import commands
import random

from subs.gastercoin import account as ac
from subs.gastercoin import blackjack as bj
from subs.gastercoin import deathmatch as dm
from subs.gastercoin import quiz

RESOURCES_DIRECTORY = './subs/gastercoin/resources/'
GASTERCOIN_CREATOR_ID_FILE = f'{RESOURCES_DIRECTORY}markovcreatorid.txt'
GASTERCOIN_HEAD_PICTURE = f'{RESOURCES_DIRECTORY}gastercoinhead.png'
GASTERCOIN_TAILS_PICTURE = f'{RESOURCES_DIRECTORY}gastercointails.png'

with open(GASTERCOIN_CREATOR_ID_FILE, 'r') as f:
    MARKOV_MODULE_CREATORS_ID = int(f.readline())

PERMISSION_ERROR_STRING = f'Error: You do not have permission to use this command.'

AUTHORIZED_CHANNELS = [340426498764832768, 408424622648721410, 340426332859269140, 464902493818585108]
VIP_PEOPLE = [293219528450637824]


class AmbiguousInputError(Exception):
    """Error raised for input that refers to multiple users"""
    def __init__(self, output):
        self.output = output


def get_member_from_guild(guild_members, username):
    """From a str username and a list of all guild members returns the member whose name contains username."""
    if username == 'rand':
        return random.choice(guild_members)
    else:
        members = []
        for member in guild_members:
            if username.lower() in member.name.replace(' ', '').lower():
                members.append(member)

        members_len = len(members)
        if members_len == 0:
            raise NameError(username)
        elif members_len == 1:
            return members[0]
        else:
            raise AmbiguousInputError([member.name for member in members])


def parse_name(guild, username):
    if '@' in username:
        try:
            return guild.get_member(int(username[3:-1]))
        except:
            raise NameError(username)
    else:
        return get_member_from_guild(guild.members, username)


class Gastercoin():
    """Defines Gastercoin commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def freemoney(self, ctx):
        """Gives the user 1000 free GasterCoins. One time use only."""
        if ac.read_account(ctx.author.id, key=ac.FREE_MONEY_KEY):
                await ctx.send(f'Error: {ctx.author.name} has already accepted their free GasterCoins.')
        else:
            ac.update_account(ctx.author.id, 1000)
            ac.update_account(ctx.author.id, 1, key=ac.FREE_MONEY_KEY)
            await ctx.send(f"Added 1000 GasterCoins to {ctx.author.name}'s account!")

    @commands.command()
    async def add(self, ctx, name, amount):
        """Generates money out of thin air!"""
        if ctx.author.id in VIP_PEOPLE:
            try:
                person_member = parse_name(ctx.guild, name)
                amount = ac.parse_int(amount)
                ac.update_account(person_member.id, amount)
                amount_formatted = '{:,}'.format(amount)
                await ctx.send(f"Added G${amount_formatted} to {person_member.name}'s account!")
            except NameError:
                await ctx.send(f'Error: {person} not found in server.')
            except AmbiguousInputError as members:
                await ctx.send(f'Error: input {person} can refer to multiple people ({members})')
            except ValueError:
                await ctx.send(f'Error: {amount} is invalid number.')

    @commands.command()
    async def remove(self, ctx, name, amount):
        """Makes money disappear!"""
        if ctx.author.id in VIP_PEOPLE:
            try:
                person_member = parse_name(ctx.guild, name)
                amount = ac.parse_int(amount)
                ac.update_account(person_member.id, -amount)
                amount_formatted = '{:,}'.format(amount)
                await ctx.send(f"Removed G${amount_formatted} from {person_member.name}'s account!")
            except NameError:
                await ctx.send(f'Error: {person} not found in server.')
            except AmbiguousInputError as members:
                await ctx.send(f'Error: input {person} can refer to multiple people ({members})')
            except ValueError:
                await ctx.send(f'Error: {amount} is invalid number.')

    @commands.command()
    async def balance(self, ctx, name=None):
        """Checks the user's balance."""
        if name is None:
            amount = '{:,}'.format(ac.read_account(ctx.author.id))
            await ctx.send(f'{ctx.author.name} has G${amount}')
        elif name == 'universe':
            await ctx.send('As all things should be.')
        else:
            try:
                person_member = parse_name(ctx.message.guild, name)
                amount = '{:,}'.format(ac.read_account(person_member.id))
                await ctx.send(f'{person_member.name} has G${amount}')
            except NameError:
                await ctx.send(f'Error: {name} not found in server.')
            except AmbiguousInputError as members:
                await ctx.send(f'Error: input {name} can refer to multiple people ({members})')

    @commands.command()
    async def leaderboard(self, ctx, name=None):
        """Allows users to easily compare each others' balances."""
        leaderboard = ac.get_balances_by_amount()
        out = '__**GasterCoin Leaderboard**__:\n'
        if name is None:
            for i in range(10):
                user_id, amount = leaderboard[i]
                amount_formatted = '{:,}'.format(amount)
                out += f'**({1 + i}) {ctx.message.guild.get_member(user_id).name}**: G${amount_formatted}\n'
            await ctx.send(out)
        else:
            if name == 'bottom':
                for i in range(len(leaderboard) - 10, len(leaderboard)):
                    user_id, amount = leaderboard[i]
                    amount_formatted = '{:,}'.format(amount)
                    out += f'**({1 + i}) {ctx.message.guild.get_member(user_id).name}**: G${amount_formatted}\n'
                await ctx.send(out)
            else:
                try:
                    name_list = [x[0] for x in leaderboard]
                    name_member = parse_name(ctx.message.guild, name)
                    name_index = name_list.index(name_member.id)
                    if name_index < 5:
                        lower = 0
                        upper = 10
                    else:
                        lower = name_index - 5
                        upper = name_index + 5
                    if name_index + 5 > len(leaderboard):
                        upper = len(leaderboard)
                        lower = len(leaderboard) - 10
                    for i in range(lower, upper):
                        user_id, amount = leaderboard[i]
                        amount_formatted = '{:,}'.format(amount)
                        out += f'**({1 + i}) {ctx.message.guild.get_member(user_id).name}**: G${amount_formatted}\n'
                    await ctx.send(out)
                except ValueError:
                    await ctx.send(f'Error: name {name} not found in leaderboard.')

    @commands.command()
    async def give(self, ctx, person, amount):
        """Donates GasterCoins from the user's account to another user's account."""
        out = ac.check_if_valid_transaction(ctx.author.id, amount)
        if out == ac.SUCCESS_STRING:
            amount = ac.parse_int(amount)
            amount_formatted = '{:,}'.format(amount)
            person = person.lower()
            try:
                person_member = parse_name(ctx.message.guild, person)
                ac.update_account(ctx.author.id, -amount)
                ac.update_account(person_member.id, amount)
                await ctx.send(f'G${amount_formatted} given to {person_member.name}!')
            except NameError:
                await ctx.send(f'Error: {person} not found in server.')
            except AmbiguousInputError as members:
                await ctx.send(f'Error: input {person} can refer to multiple people ({members})')
        else:
            await ctx.send(out)

    @commands.command(aliases=['flip'])
    async def flip_coin(self, ctx, bet, coin_side='h'):
        """Bets GasterCoins on a coin flip."""
        if bet == 'table':
            await ctx.send('(╯°□°）╯︵ ┻━┻')
        else:
            out = ac.check_if_valid_transaction(ctx.author.id, bet)
            if out == ac.SUCCESS_STRING:
                if 'h' in coin_side or 't' in coin_side:
                    bet = ac.parse_int(bet)
                    cutoff = 50
                    if 'h' in coin_side:
                        cutoff -= 5
                    else:
                        cutoff += 5
                    coin = random.randint(0, 100)

                    if coin <= cutoff:
                        picture = GASTERCOIN_HEAD_PICTURE
                    else:
                        picture = GASTERCOIN_TAILS_PICTURE

                    if 'h' in coin_side and coin <= cutoff or 't' in coin_side and coin > cutoff:
                        ac.update_account(ctx.author.id, bet)
                        out = "You won! "
                    else:
                        ac.update_account(ctx.author.id, -bet)
                        out = "You lost. "
                    amount = '{:,}'.format(ac.read_account(ctx.author.id))
                    out += f"{ctx.author.name}'s balance is now G${amount}."
                    if ctx.channel.id in AUTHORIZED_CHANNELS:
                        await ctx.send(out, file=discord.File(picture))
                    else:
                        if coin == 0:
                            await ctx.send('Coin is heads. ' + out)
                        else:
                            await ctx.send('Coin is tails. ' + out)
                else:
                    await ctx.send(f'Error: {coin_side} is not a valid coin side.')
            else:
                await ctx.send(out)

    @commands.group(invoke_without_command=True)
    async def quiz(self, ctx, *args):
        """Gives users GasterCash in exchange for correct answers."""
        question_args = quiz.get_question(args)
        difficulty = question_args[0]
        category = question_args[1]
        question = question_args[2]
        answer = question_args[3]

        await ctx.send(f"This {category} question of difficulty {difficulty} is for {ctx.author.name}. " + question)

        while True:
            message = await self.bot.wait_for('message')
            if message.author == ctx.author:
                if any([message.content.lower() == x.lower() for x in answer]):
                    amount_won = 10 ** (difficulty + 3)
                    amount_formatted = '{:,}'.format(amount_won)
                    ac.update_account(ctx.author.id, amount_won)
                    await ctx.send(f"Answer {answer[0]} is correct! "
                                   f"{ctx.author.name}'s balance has increased by G${amount_formatted}!")
                    break
                else:
                    await ctx.send(f"Answer {message.content} is incorrect. Correct answer was {answer[0]}.")
                    break

    @quiz.command(name='categories')
    async def _categories(self, ctx):
        await ctx.send(quiz.QUESTION_CATEGORIES)

    @quiz.command(name='challenge')
    async def _challenge(self, ctx, opponent, bet='0'):
        out = ac.check_if_valid_transaction(ctx.author.id, bet, zero_valid=True)
        if out == ac.SUCCESS_STRING:
            bet = ac.parse_int(bet)
            try:
                opponent_member = parse_name(ctx.message.guild, opponent)
            except NameError:
                await ctx.send(f'Error: {opponent} not found in server.')
                return
            except AmbiguousInputError as members:
                await ctx.send(f'Error: input {opponent} can refer to multiple people ({members})')
                return
            out = ac.check_if_valid_transaction(opponent_member.id, bet, username=opponent_member.name, zero_valid=True)
            if out == ac.SUCCESS_STRING:
                bet_formatted = '{:,}'.format(bet)
                ac.update_account(ctx.author.id, -bet)
                out = f'A competition has been set up between {ctx.author.name} and {opponent_member.mention} ' \
                      f'with bet G${bet_formatted}! To confirm this, {opponent_member.name} ' \
                      f'must react to this message with a :thumbsup: in the next minute. ' \
                      f'If a minute passes or if the challenger reacts to this message, ' \
                      f'the competition will be cancelled and the deposit refunded.'
                msg = await ctx.send(out)
                await msg.add_reaction('\N{THUMBS UP SIGN}')
                match_accepted = False
                while True:
                    try:
                        reaction, user = await self.bot.wait_for('reaction_add', timeout=60)
                        if str(reaction.emoji) == '👍' and user == opponent_member:
                            ac.update_account(opponent_member.id, -bet)
                            match_accepted = True
                            break
                        elif user == ctx.author:
                            ac.update_account(ctx.author.id, bet)
                            await msg.edit(content=f'{ctx.author.name} has declined their challenge '
                                                   f'and the deposit of G${bet_formatted} has been returned.')
                            break
                    except asyncio.TimeoutError:
                        ac.update_account(ctx.author.id, bet)
                        await msg.edit(content=f'One minute has passed and the competition has been cancelled. '
                                               f'The deposit of G${bet_formatted} has been returned.')
                        break

                if match_accepted:
                    author_score = 0
                    opponent_score = 0
                    round_number = 1

                    while True:
                        question_and_answer = quiz.get_question(tuple('1'))
                        question = question_and_answer[0]
                        answer = question_and_answer[1]
                        header = f'__**Quiz Game Show Thing**__\n**' \
                                 f'Round {round_number}**\n\n' \
                                 f'__Current Score__:\n' \
                                 f'__{ctx.author.name}__: {author_score}\n' \
                                 f'__{opponent_member.name}__: {opponent_score}\n\n'
                        question_message = header + str(question)

                        msg = await ctx.send(question_message)

                        while True:
                            try:
                                message = await self.bot.wait_for('message', timeout=10)
                                if message.author == ctx.author or message.author == opponent_member:
                                    if any([message.content.lower() == x.lower() for x in answer]):
                                        if message.author == ctx.author:
                                            author_score += 1
                                        else:
                                            opponent_score += 1
                                        await msg.edit(content=f"{question_message} Answer {answer[0]} is correct! "
                                                       f"{message.author.name}'s score has increased by 1!")
                                        break
                            except asyncio.TimeoutError:
                                await msg.edit(content=f'{question_message} Nobody has correctly answered this '
                                                       f'question. The correct answer was {answer[0]}.')
                                break
                        if author_score == quiz.QUIZ_TARGET_SCORE:
                            ac.update_account(ctx.author.id, (2 * bet))
                            await ctx.send(f'**{ctx.author.name} has won G${bet_formatted}!**')
                            break
                        elif opponent_score == quiz.QUIZ_TARGET_SCORE:
                            ac.update_account(opponent_member.id, (2 * bet))
                            await ctx.send(f'**{opponent_member.name} has won G${bet}!**')
                            break
                        round_number += 1
            else:
                await ctx.send(out)
        else:
            await ctx.send(out)

    @commands.group(aliases=['dm'], invoke_without_command=True)
    async def deathmatch(self, ctx, opponent='rand', bet=None):
        """Allows users to duke it out in a 1v1 match."""
        if bet is not None:
            out = ac.check_if_valid_transaction(ctx.author.id, bet)
            if out == ac.SUCCESS_STRING:
                bet = ac.parse_int(bet)
                try:
                    opponent_member = parse_name(ctx.message.guild, opponent)
                except NameError:
                    await ctx.send(f'Error: {opponent} not found in server.')
                    return
                except AmbiguousInputError as members:
                    await ctx.send(f'Error: input {opponent} can refer to multiple people ({members})')
                    return
                out = ac.check_if_valid_transaction(opponent_member.id, bet, username=opponent_member.name)
                if out == ac.SUCCESS_STRING:
                    bet_formatted = '{:,}'.format(bet)
                    ac.update_account(ctx.author.id, -bet)
                    out = f'Deathmatch set up between {ctx.author.name} and {opponent_member.mention} with bet ' \
                          f'G${bet_formatted}! To confirm this match, {opponent_member.name} must react to ' \
                          f'this message with a :thumbsup: in the next minute. If a minute passes or if the ' \
                          f'challenger reacts to this message, the deathmatch will be cancelled and the deposit ' \
                          f'refunded.'
                    msg = await ctx.send(out)
                    await msg.add_reaction('\N{THUMBS UP SIGN}')

                    while True:
                        try:
                            reaction, user = await self.bot.wait_for('reaction_add', timeout=60)
                            if str(reaction.emoji) == '👍' and user == opponent_member:
                                deathmatch_messages = dm.do_deathmatch(ctx.author, opponent_member, bet=bet_formatted)
                                ac.update_account(deathmatch_messages[-1], (2 * bet))
                                for message in deathmatch_messages[:-1]:
                                    await msg.edit(content=message)
                                    await asyncio.sleep(1)
                                break
                            elif user == ctx.author:
                                ac.update_account(ctx.author.id, bet)
                                await msg.edit(content=f'{ctx.author.name} has declined their challenge '
                                                       f'and the deposit of G${bet_formatted} has been returned.')
                                return
                        except asyncio.TimeoutError:
                            ac.update_account(ctx.author.id, bet)
                            await msg.edit(content=f'One minute has passed and the deathmatch has been cancelled. '
                                                   f'The deposit of G${bet_formatted} has been returned.')
                            return
                else:
                    await ctx.send(out)
            else:
                await ctx.send(out)
        else:
            try:
                opponent_member = parse_name(ctx.message.guild, opponent)
            except NameError:
                await ctx.send(f'Error: {opponent} not found in server.')
                return
            except AmbiguousInputError as members:
                await ctx.send(f'Error: input {opponent} can refer to multiple people ({members})')
                return
            msg = await ctx.send(dm.DEATHMATCH_HEADER)
            deathmatch_messages = dm.do_deathmatch(ctx.author, opponent_member)
            for message in deathmatch_messages[:-1]:
                await msg.edit(content=message)
                await asyncio.sleep(1)

    @deathmatch.command(name='special')
    async def _special(self, ctx, *args):
        """Lets user add a custom special attack in deathmatches."""
        if args != ():
            if args[0].lower() == 'edit':
                attack = ' '.join(args[1:])
                ac.update_account(ctx.author.id, attack, key=ac.SPECIAL_MOVE_KEY)
                await ctx.send(f"{ctx.author.name}'s special move updated to: $P1 deals a heavy blow to $P2 by __"
                               f"**{attack}**__!!!")
            else:
                await ctx.send(f"{ctx.author.name}'s current special move: $P1 deals a heavy blow to $P2 by "
                               f"__**{ac.read_account(ctx.author.id, key=ac.SPECIAL_MOVE_KEY)}**__!!!")
        else:
            await ctx.send(f"{ctx.author.name}'s current special move: $P1 deals a heavy blow to $P2 by "
                           f"__**{ac.read_account(ctx.author.id, key=ac.SPECIAL_MOVE_KEY)}**__!!!")

    @commands.command(aliases=['bj'])
    async def blackjack(self, ctx, bet):
        """Bets GasterCoins on a VERY SIMPLIFIED STUPIFIED VERSION of Blackjack."""
        out = ac.check_if_valid_transaction(ctx.author.id, bet)
        if out == ac.SUCCESS_STRING:
            bet = ac.parse_int(bet)
            bet_formatted = '{:,}'.format(bet)
            ac.update_account(ctx.author.id, -bet)
            await ctx.send(f'*Game of Blackjack started by {ctx.author.name} with bet G${bet_formatted}*')
            dealer_hand, player_hand = bj.init_hands()
            if bj.get_value(player_hand) == 21:
                ac.update_account(ctx.author.id, bet)
                bet = round(bet * 1.5)
                bet_formatted = '{:,}'.format(bet)
                ac.update_account(ctx.author.id, bet)
                out = bj.print_hands(dealer_hand, player_hand, ctx.author.name, len(dealer_hand))
                out += f'**{ctx.author.name} has a blackjack and gets a payout of G${bet_formatted}!**'
                await ctx.send(out)
            else:
                dealer_cards = 2
                while True:
                    out = bj.print_hands(dealer_hand, player_hand, ctx.author.name,
                                         dealer_cards=dealer_cards, hide_dealer=True)
                    out += 'Will you hit or stand?'
                    await ctx.send(out)

                    while True:
                        message = await self.bot.wait_for('message')
                        if message.author == ctx.author and \
                                (bj.HIT in message.content.lower() or bj.STAND in message.content.lower()):
                            break

                    if bj.HIT in message.content.lower():
                        player_hand = bj.hit(player_hand)
                        if bj.get_value(player_hand) > 21:
                            break
                    else:
                        break
                    dealer_cards += 1

                out = bj.print_hands(dealer_hand, player_hand, ctx.author.name, len(dealer_hand))
                if bj.is_winner(player_hand, dealer_hand):
                    ac.update_account(ctx.author.id, 2 * bet)
                    out += f'**{ctx.author.name} has won G${bet_formatted}**!'
                else:
                    if bj.get_value(player_hand) > 21:
                        out += f'**{ctx.author.name} has bust and lost G${bet_formatted}**'
                    elif bj.get_value(player_hand) == bj.get_value(dealer_hand):
                        ac.update_account(ctx.author.id, bet)
                        out += f'**The hands are the same value and the bet of G${bet_formatted} has been pushed.**'
                    else:
                        out += f'**{ctx.author.name} has less than the dealer and lost G${bet_formatted}**'
                await ctx.send(out)
        else:
            await ctx.send(out)


def setup(bot):
    """Adds the cog to the bot."""
    bot.add_cog(Gastercoin(bot))

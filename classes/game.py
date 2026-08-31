import json
from datetime import datetime, date
from dataclasses import dataclass, field
from typing import ClassVar, Dict, List

class DataLoader:
        """Loads data stored in JSON files in assets folder.""" 

        @classmethod     
        def load(cls):

            try:
                with open("assets/words.json") as f:
                    Word.all_words = json.load(f)

                with open("assets/letter_values.json") as f:
                    Word.letter_values = json.load(f)

                with open("assets/itwords.json") as f:
                    ItWord.all_itwords = json.load(f)

                with open("assets/rules.json") as f:
                    rules = json.load(f)
                    return rules

            except FileNotFoundError as e:
                raise FileNotFoundError("No such file or directory")

 
@dataclass(frozen=True)
class Word:
    """Loads a Dict of all valid words of 3-8 letters and the corresponding scrabble score"""
    word: str
    value: int = 0

    all_words: ClassVar[Dict[str, int]] = {}
    letter_values: ClassVar[Dict[str, int]] = {}

    def word_value(self) -> int:
        """Calculate the value of a word using letter_values."""
        return sum(Word.letter_values[letter] for letter in self.word)


@dataclass(frozen=True)
class ItWord:
    """Loads a list of all valid ItWords"""
    word: str
    all_itwords: ClassVar[List[str]] = []

    day_zero: ClassVar[date] = date(2026, 8, 1)

    @classmethod
    def get_itword(cls, d: date) -> str:
        """Returns the ItWord for a given date, with the date equating to an index in the list."""
        index = (d - cls.day_zero).days

        if index < 0:
            raise ValueError("Date is before day_zero.")
        if index >= len(cls.all_itwords):
            raise ValueError("All ItWords used")

        return cls.all_itwords[index]


@dataclass
class GameSession:
    """Tracks session analytics and returns length of session when it ends"""
    user: int
    start: datetime = field(default_factory=datetime.now)
    end: datetime | None = None
    total_guesses: int = 0
    word_score: int = 0
 
    @property
    def session_length(self) -> float | None:
        return round((self.end - self.start).total_seconds(), 1) if self.end else None 


@dataclass
class Guess:
    """Ensures user input matches JSON format and returns valid boolean"""
    gamesession: GameSession
    guess: str

    def __post_init__(self):
        self.guess = self.guess.upper() 
        self.gamesession.total_guesses += 1

        if self.valid:
            self.gamesession.word_score += Word(self.guess).word_value()
     
    @property
    def valid(self) -> bool:
        return self.guess in Word.all_words


class Game:
    def __init__(self):
        self.date = date.today()

    def get_user_guess(self):
        """Returns a correctly formatted word to print to screen."""
        dash_string = " _ " * (self.round)

        if self.round <= 4:
            word = f"{self.itword[self.round]} _ {dash_string}{self.itword[self.round+1]}: "

        else:
            word = f"{self.itword[self.round]}{dash_string} _ : "

        return input(word)

    def play_rounds(self):
        while self.round <= 5:
            self.user_guess = Guess(self.game_session, self.get_user_guess())        

            if self.user_guess.valid:

                if self.round <= 4:
                    if self.user_guess.guess[0] == self.itword[self.round] and self.user_guess.guess[-1] == self.itword[self.round+1]:
                        self.round += 1 

                else:
                    if self.user_guess.guess[0] == self.itword[self.round]: 
                        break  
           
    def run(self):
        """Run from main.py"""
        DataLoader.load()        
        self.user = 12345 
        self.game_session = GameSession(self.user)  
        self.round = 0  
        self.itword = ItWord.get_itword(self.date)

        self.play_rounds() 

        self.game_session.end = datetime.now()  

        print(f"Number of guesses: {self.game_session.total_guesses}")
        print(f"Total word score: {self.game_session.word_score}")
        print(f"Time to complete:  {self.game_session.session_length} seconds")  


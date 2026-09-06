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

                with open("assets/itword_archive.json") as f:
                    ItWord.archive = {date.fromisoformat(d): w for d, w in json.load(f).items()}

                with open("assets/rules.json") as f:
                    rules = json.load(f)
                    return rules

            except FileNotFoundError as e:
                raise FileNotFoundError("No such file or directory")

 
@dataclass(frozen=True)
class Word:
    """Loads a list of all valid words of 3-8 letters plus a dict of all letters and their corresponding points value"""
    word: str
    word_value: int = 0

    all_words: ClassVar[List[str]] = []
    letter_values: ClassVar[Dict[str, int]] = {}

    def value(self) -> int:
        """Calculate the value of a word using letter_values."""
        return sum(Word.letter_values[letter] for letter in self.word)


@dataclass(frozen=True)
class ItWord:
    """Loads a list of all valid ItWords."""
    all_itwords: ClassVar[List[str]] = []
    archive: ClassVar[Dict[date, str]] = {}

    day_zero: ClassVar[date] = date(2026, 9, 1)  # Starting date for all_itwords cycling

    @classmethod
    def save(cls):
        """Saves itword_archive to JSON file."""
        with open("assets/itword_archive.json", "w") as file:
            json.dump({date.isoformat(): word for date, word in cls.archive.items()}, file, indent=4)

    @classmethod
    def get_itword(cls, date: date) -> str:
        """Returns the ItWord for a given date, saves it to itword_archive if not already present."""
        if date in cls.archive:
            return cls.archive[date]
        
        index = (date - cls.day_zero).days % len(cls.all_itwords) #this ensures all_itwords is continually cycled through        
        itword = cls.all_itwords[index]        
        cls.archive[date] = itword 
        cls.save() #saves updated itword_archive to JSON file

        return itword


@dataclass
class GameSession:
    """Tracks session analytics and returns length of session when it ends"""
    user: int
    start: datetime = field(default_factory=datetime.now)
    end: datetime | None = None
    total_guesses: int = 0
    word_length: int = 3
    round = 0  
    first_letter = 0
    last_letter = 1
    total_score: int = 0
    valid_guessed_words: Dict[str, int] = field(default_factory=dict)
 
    def duration(self):
        if not self.end:
            return None
        
        session_length = int((self.end - self.start).total_seconds())
        minutes = session_length // 60
        seconds = session_length % 60
        
        self.total_score -= minutes  # Subtract 1 point for each minute taken to complete the game

        return minutes, seconds #only returns minutes and seconds to print to screen in Game.run method


@dataclass
class Guess:
    """Ensures user input matches JSON format and returns valid boolean"""
    gamesession: GameSession
    itword: str
    user_guess: str
    
    def __post_init__(self):
        self.user_guess = self.user_guess.upper() 
        self.gamesession.total_guesses += 1

        if self.valid:
            value = Word(self.user_guess).value()
            self.gamesession.total_score += value
            self.gamesession.valid_guessed_words[self.user_guess] = value
            self.gamesession.word_length += 1    
            self.gamesession.round += 1   
            self.gamesession.first_letter += 1  
            if self.gamesession.round <= 4:
                self.gamesession.last_letter += 1      

        else:
          self.gamesession.total_score -= 1  # Subtract 1 point for each incorrect guess made         

    @property
    def first_letter(self) -> int:
        return self.gamesession.first_letter

    @property
    def last_letter(self) -> int:
        return self.gamesession.last_letter

    @property
    def rounds(self) -> int:
        return self.gamesession.round
     
    @property
    def valid(self) -> bool:
        guess = self.user_guess

        return (
            guess in Word.all_words
            and len(guess) == self.gamesession.word_length
            and guess[0] == self.itword[self.first_letter]
            and (self.rounds >= 5 or guess[-1] == self.itword[self.last_letter])
    )   


class Game:
    def __init__(self):
        self.date = date.today()

    def get_user_guess(self):
        """Returns a correctly formatted word to print to screen for user to input guess."""
        dash_string = " _ " * (self.game_session.round)

        if self.game_session.round <= 4:
            word = f"{self.itword[self.game_session.first_letter]} _ {dash_string}{self.itword[self.game_session.last_letter]}: "

        else:
            word = f"{self.itword[self.game_session.first_letter]}{dash_string} _  _: "

        return input(word)    
         
    def run(self):
        """Run from main.py"""
        DataLoader.load()        
        self.user_ID = 12345 
        self.game_session = GameSession(self.user_ID)  
        self.itword = ItWord.get_itword(self.date)

        while self.game_session.round <= 5:
            self.input = Guess(self.game_session, self.itword, self.get_user_guess())  

        self.game_session.end = datetime.now()  
        minutes, seconds = self.game_session.duration()  #session duration details only required to print to screen

        print(f"You correctly entered: {self.game_session.valid_guessed_words}")    
        print(f"Number of guesses in total: {self.game_session.total_guesses}")  
        print(f"Time to complete: {minutes} min {seconds} sec") 
        print(f"Total score: {self.game_session.total_score} points")
    


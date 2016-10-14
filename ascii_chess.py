from common import *
from piece import *
from board import *
from move import *


class StopError(Exception):
	pass


class Game:

	def __init__(self):
		self._board = Board.initial_position()
		self._half_move = 1
		self._move_list = []

	def loop(self):
		print
		self._board.dump()
		while True:
			try:
				input = raw_input("\nEnter a move for {} ('q' to quit, 'b' to print board): ".format(self.side_to_move()))
				self.handle_input(input.strip())
			except ValueError as ve:
				print str(ve)
			except InvalidMoveError as ime:
				print str(ime)
			except StopError:
				break

	def handle_input(self, input, interactive = True, print_board = True):
			if input == 'q':
				if interactive:
					raise StopError
			elif input == 'b':
				if interactive:
					self._board.dump()
			elif input == 'load':
				if interactive:
					file_name = raw_input("Enter file name: ")
					if len(file_name):
						self.load_file(file_name)
			elif input == 'save':
					file_name = raw_input("Enter file name: ")
					if len(file_name):
						self.save_moves_to_file(file_name)
			else:
				expected_color = self.side_to_move()
				move = self._board.parse_move(input, expected_color)
				move.update_board(self._board, expected_color)
				self._half_move += 1
				self._move_list.append(input)
				if print_board:
					self._board.dump()

	def load_file(self, file_name):
		try:
			with open(file_name) as f:
				for line in (ln.strip() for ln in f if len(ln)):
					print line
					moves = line.split()
					self.handle_input(moves[0], False, False)
					if len(moves) > 1:
						self.handle_input(moves[1], False, False)
			print '\n'
			self._board.dump()
		except IOError as err:
			print err

	def save_moves_to_file(self, file_name):
		try:
			with open(file_name, "w") as f:
				n = 0
				for mv in self._move_list:
					n += 1
					f.write(mv)
					if (n % 2):
						f.write("\t")
					else:
						f.write("\n")
		except IOError as err:
			print err


	def side_to_move(self):
		"""Returns WHITE or BLACK depending on which side is to move."""
		return WHITE if (self._half_move % 2) else BLACK


if __name__ == '__main__':
	game = Game()
	game.loop()
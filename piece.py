from common import *
from abc import ABCMeta, abstractmethod

class Piece:

	__metaclass__ = ABCMeta

	def __init__(self, name, abbrev, value, color):
		self._name = name
		self._abbrev = abbrev
		self._value = value
		self._color = color
		self._has_moved = False

	def __str__(self):
		return self.abbrev()

	def abbrev(self):
		if self.is_white():
			return self._abbrev.upper()
		else:
			return self._abbrev.lower()

	def get_color(self):
		"""Returns the color of this piece (WHITE or BLACK)."""
		return self._color

	def is_white(self):
		return self._color == WHITE

	def is_same_color(self, other):
		return self._color == other._color

	def set_has_moved(self, moved = True):
		self._has_moved = moved

	def has_moved(self):
		"""Checks if this piece has moved."""
		return self._has_moved

	def is_valid_move(self, board, start, to):
		"""Checks if suggested move is valid for this piece, on the given chess board. from and to
		are the current square and the destination square, respectively. Only non-capturing moves
		are considered, i.e. this method will return False if the target square is occupied by
		another piece."""
		return self.is_covering_square(board, start, to) and board.is_empty(to)

	def is_valid_capture(self, board, start, to):
		"""Checks if the suggested move is a valid capturing move for this piece. from and to
		are the current square and the destination square, respectively. The target square must
		be occupied by a piece of the opposite color for this method to return True."""
		return self.is_covering_square(board, start, to) and board.is_piece_of_opposite_color(to, self)

	def is_covering_square(self, board, square, target):
		"""Checks if this piece is covering the given target, when standing on the given square on 
		the given board."""
		moves = self.move_generator(square, target)
		if moves is None:
			return False
		for sq in moves:
			# If we encounter a piece before we reach the target square, the capture
			# is blocked.
			if sq == target:
				return True
			if not board.is_empty(sq):
				break
		return False

	@abstractmethod
	def move_generator(self, board, start, to):
		pass


class Pawn(Piece):

	def __init__(self, color):
		Piece.__init__(self, 'pawn', 'p', 1, color)
		self._en_passant = None

	def is_valid_move(self, board, start, to):
		if not board.is_empty(to):
			return False
		from_rank = start.rank()
		to_rank = to.rank()
		rank_diff = to_rank - from_rank
		if rank_diff == 0 or abs(rank_diff) > 2:
			return False
		# At this point we know that abs(rank_diff) is 1 or 2
		file_diff = to.file() - start.file()
		if abs(file_diff) > 1:
			return False
		if file_diff == 0:
			# This represents a non-capturing move
			if not board.is_empty(to):
				return False
			if self.is_white():
				return (rank_diff == 1) or (rank_diff == 2 and from_rank == 2 and 
					board.is_empty(Square.fromFileAndRank(start.file(), 3))) 
			else:
				return (rank_diff == -1) or (rank_diff == -2 and from_rank == 7 and 
					board.is_empty(Square.fromFileAndRank(start.file(), 6)))
		else:
			# This represents a (potential) capturing move
			if board.is_empty(to):
				# Nothing to capture, so this is not allowed
				return False
			captured_piece = board.get_piece(to)
			if self.is_same_color(captured_piece):
				return False
			# Now we know that the target square contains a piece of the opposite color.
			# All that's left is to verify that the pawn moved in the right direction
			# vertically
			if self.is_white():
				return rank_diff == 1
			else:
				return rank_diff == -1

	def is_valid_capture(self, board, start, to):
		if (self._en_passant is not None) and (to == self._en_passant):
			return True
		return self.is_covering_square(board, start, to) and board.is_piece_of_opposite_color(to, self)

	def is_covering_square(self, board, square, target):
		req_rank_diff = 1 if self.is_white() else -1
		return (target.rank() - square.rank() == req_rank_diff) and (abs(target.file() - square.file()) == 1)

	def set_en_passant_square(self, square):
		"""Sets a square that is an allowed target for an en passant move for this pawn, if any."""
		self._en_passant = square

	def can_be_promoted(self, square):
		"""Checks if this pawn can be promoted, i.e. if it has reached the opposite side of the board."""
		if self.is_white():
			return square.rank() == 8
		else:
			return square.rank() == 1

	def move_generator(self, start, to):
		return None


class Rook(Piece):

	def __init__(self, color):
		Piece.__init__(self, 'rook', 'r', 5, color)

	def move_generator(self, start, to):
		"""Internal method that returns a generator of moves, given a start and an end position 
		on an empty board. Returns None if the move would violate the rules for Rook moves."""
		rank_diff = start.rank() - to.rank()
		file_diff = start.file() - to.file()
		if rank_diff != 0 and file_diff != 0:
			# One of the rank or the file must remain unchanged
			return None
		if rank_diff == 0:
			return horizontal_move_generator(start, to)
		else:
			return vertical_move_generator(start, to)


class Knight(Piece):

	def __init__(self, color):
		Piece.__init__(self, 'knight', 'n', 3, color)

	def is_covering_square(self, board, square, target):
		file_diff = abs(target.file() - square.file())
		rank_diff = abs(target.rank() - square.rank())
		if file_diff == 1:
			if rank_diff != 2:
				return False
		elif rank_diff == 1:
			if file_diff != 2:
				return False
		else:
			return False
		return True		

	def move_generator(self, start, to):
		return None


class Bishop(Piece):

	def __init__(self, color):
		Piece.__init__(self, 'bishop', 'b', 3, color)

	def move_generator(self, start, to):
		"""Internal method that returns a generator of moves, given a start and an end position 
		on an empty board. Returns None if the move would violate the rules for Rook moves."""
		file_diff = to.file() - start.file()
		rank_diff = to.rank() - start.rank()
		if file_diff == 0 or rank_diff == 0:
			return None
		if abs(file_diff) != abs(rank_diff):
			return None
		return diagonal_move_generator(start, to)


class Queen(Piece):

	def __init__(self, color):
		Piece.__init__(self, 'queen', 'q', 9, color)

	def move_generator(self, start, to):
		rank_diff = to.rank() - start.rank()
		file_diff = to.file() - start.file()
		if rank_diff == 0:
			return horizontal_move_generator(start, to) if (abs(file_diff) > 0) else None
		if file_diff == 0:
			return vertical_move_generator(start, to) if (abs(rank_diff) > 0) else None
		if abs(rank_diff) == abs(file_diff):
			return diagonal_move_generator(start, to)
		return None


class King(Piece):
	
	def __init__(self, color):
		Piece.__init__(self, 'king', 'k', 0, color)

	def is_valid_move(self, board, start, to):
		if start == to:
			return False
		if abs(to.file() - start.file()) <= 1 and abs(to.rank() - start.rank()) <= 1:
			return board.is_empty(to)
		# Check castling
		rank = 1 if self.is_white() else 8
		if not ((start.rank() == rank and to.rank() == rank) and (start.file() == 5 and (to.file() == 1 or to.file() == 8))):
			return False
		if self.has_moved() or not board.is_rook(to, self.get_color()):
			return False
		rook = board.get_piece(to)
		if rook.has_moved():
			return False
		return self.is_path_clear_for_castling(board, rank, to.file())

	def is_covering_square(self, board, square, target):
		if square == target:
			return False
		return abs(target.file() - square.file()) <= 1 and abs(target.rank() - square.rank()) <= 1

	def is_path_clear_for_castling(self, board, rank, end_file):
		start_file = 5
		step = 1 if end_file > start_file else -1
		for f in range(start_file + step, end_file, step):
			sq = Square.fromFileAndRank(f, rank)
			# TODO: Check if the square is under attack.
			if not board.is_empty(sq):
				return False
		return True

	def move_generator(self, start, to):
		return None


PIECE_TYPES = {'K': King, 'Q': Queen, 'R': Rook, 'B': Bishop, 'N': Knight, 'P': Pawn}

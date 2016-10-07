from abc import ABCMeta, abstractmethod

# TODO: The is_valid_move implementations does not take into account 
# positions where the King ends up in check.

WHITE = "white"
BLACK = "black"

FILES = [ 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h' ]
RANKS = [ 1, 2, 3, 4, 5, 6, 7, 8 ]

class Square:

	def __init__(self, coordinate):
		file = coordinate[:1]
		if not file in FILES:
			err = "Not a valid file: '{0}' (requires 'a' to 'h')".format(file)
			raise ValueError(err)
		rank = int(coordinate[1:])
		if not rank in RANKS:
			err = "Not a valid rank: {0} (requires 1 to 8)".format(rank)
			raise ValueError(err)
		self._file = file
		self._file_no = FILES.index(file) + 1
		self._rank = rank

	@staticmethod
	def fromFileAndRank(file, rank):
		if isinstance(file, int):
			return Square(FILES[file - 1] + str(rank))	
		else:
			return Square(file + str(rank))

	def rank(self):
		"""Returns the rank, as a number between 1 and 8."""
		return self._rank

	def file(self):
		"""Returns the file, as a number between 1 and 8."""
		return self._file_no

	def __str__(self):
		return str(self._file) + str(self._rank)

	def __repr__(self):
		return "Square('{0}{1}')".format(self._file, self._rank)

	def __hash__(self):
		return hash((self._file, self._rank))

	def __eq__(self, other):
		return (self._file == other._file) and (self._rank == other._rank)

	def __ne__(self, other):
		return not(self == other)


def horizontal_move_generator(start, to):
	file_diff = to.file() - start.file()
	step = 1 if (file_diff > 0) else -1
	for f in range(start.file() + step, to.file() + step, step):
		yield Square.fromFileAndRank(f, start.rank())

def vertical_move_generator(start, to):
	rank_diff = to.rank() - start.rank()
	step = 1 if (rank_diff > 0) else -1
	for r in range(start.rank() + step, to.rank() + step, step):
		yield Square.fromFileAndRank(to.file(), r)

def diagonal_move_generator(start, to):
	file_step = 1 if (to.file() > start.file()) else -1
	rank_step = 1 if (to.rank() > start.rank()) else -1
	pairs = zip(range(start.file() + file_step, to.file() + file_step, file_step),
		range(start.rank() + rank_step, to.rank() + rank_step, rank_step))
	for p in pairs:
		yield Square.fromFileAndRank(*p)


class Piece:

	__metaclass__ = ABCMeta

	def __init__(self, name, abbrev, value, color):
		self._name = name
		self._abbrev = abbrev
		self._value = value
		self._color = color

	def __str__(self):
		return self.abbrev()

	def abbrev(self):
		if self.is_white():
			return self._abbrev.upper()
		else:
			return self._abbrev.lower()

	def is_white(self):
		return self._color == WHITE

	def is_same_color(self, other):
		return self._color == other._color

	@abstractmethod
	def move_generator(self, board, start, to):
		pass

	def is_valid_move(self, board, start, to):
		"""Checks if suggested move is valid for this piece, on the given chess board. from and to
		are the current square and the destination square, respectively."""
		moves = self.move_generator(start, to)
		if moves is None:
			return False
		for sq in moves:
			if board.is_empty(sq):
				continue
			# The move is allowed only if sq == to, and it is occupied by a piece
			# of the opposite color
			if sq != to:
				# There is a piece in the way, blocking us.
				return False
			else:
				other_piece = board.get_piece(sq)
				return not other_piece.is_same_color(self)
		return True


class Pawn(Piece):

	def __init__(self, color):
		Piece.__init__(self, 'pawn', 'p', 1, color)
		self._en_passant = None

	def is_valid_move(self, board, start, to):
		if (self._en_passant is not None) and (to == self._en_passant):
			return True
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
				return (file_diff == 1) or (file_diff == 2 and from_rank == 2)
			else:
				return (file_diff == -1) or (file_diff == -2 and from_rank == 7)
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

	def is_valid_move(self, board, start, to):
		file_diff = abs(to.file() - start.file())
		rank_diff = abs(to.rank() - start.rank())
		if file_diff == 1:
			if rank_diff != 2:
				return False
		elif rank_diff == 1:
			if file_diff != 2:
				return False
		else:
			return False
		# At this point we've verified that the move fulfills the rule for how
		# Knights move on the board. Now we just need to verify that the end square
		# is either empty or occupied by a piece of the opposite color.
		if board.is_empty(to):
			return True
		else:
			other_piece = board.get_piece(to)
			return not other_piece.is_same_color(self)

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
			return horizontal_move_generator(start, to) if (file_diff > 0) else None
		if file_diff == 0:
			return vertical_move_generator(start, to) if (rank_diff > 0) else None
		if abs(rank_diff) == abs(file_diff):
			return diagonal_move_generator(start, to)
		return None


class King(Piece):
	
	def __init__(self, color):
		Piece.__init__(self, 'king', 'k', 0, color)

	def is_valid_move(self, board, start, to):
		if start == to:
			return False
		if not board.is_empty(to):
			return False
		return abs(to.file() - start.file()) <= 1 and abs(to.rank() - start.rank()) <= 1

	def move_generator(self, start, to):
		return None


class Board:

	def __init__(self):
		self._squares = {}

	@staticmethod
	def initial_position():
		b = Board()
		b.setup_initial_position()
		return b

	def add_piece(self, p, s):
		"""Adds the piece p to the square s."""
		self._squares[s] = p

	def get_piece(self, square):
		"""Returns the piece currently occupying the given square."""
		return self._squares[square]

	def is_empty(self, square):
		"""Checks if the given square is empty."""
		return square not in self._squares

	def setup_initial_position(self):
		"""Creates a board with the initial position for a game of chess."""
		self._squares = {}
		# Fill the second rank with white pawns, and the seventh rank with black pawns:
		for f in FILES:
			self.add_piece(Pawn(WHITE), Square(f + "2"))
			self.add_piece(Pawn(BLACK), Square(f + "7"))
		# Place the Rooks:
		self.add_piece(Rook(WHITE), Square('a1'))
		self.add_piece(Rook(WHITE), Square('h1'))
		self.add_piece(Rook(BLACK), Square('a8'))
		self.add_piece(Rook(BLACK), Square('h8'))
		# Place the Knights:
		self.add_piece(Knight(WHITE), Square('b1'))
		self.add_piece(Knight(WHITE), Square('g1'))
		self.add_piece(Knight(BLACK), Square('b8'))
		self.add_piece(Knight(BLACK), Square('g8'))
		# Place the Bishops:
		self.add_piece(Bishop(WHITE), Square('c1'))
		self.add_piece(Bishop(WHITE), Square('f1'))
		self.add_piece(Bishop(BLACK), Square('c8'))
		self.add_piece(Bishop(BLACK), Square('f8'))
		# Place the Queens:
		self.add_piece(Queen(WHITE), Square('d1'))
		self.add_piece(Queen(BLACK), Square('d8'))
		# And lastly the Kings:
		self.add_piece(King(WHITE), Square('e1'))
		self.add_piece(King(BLACK), Square('e8'))

	def dump(self):
		print "   ",
		for f in FILES:
			print f.upper(),
		print "    "
		print "-" * 23
		for r in range(8, 0, -1):
			print str(r) + " |",
			for f in FILES:
				sq = Square.fromFileAndRank(f, r)
				if self.is_empty(sq):
					print 'o',
				else:
					p = self.get_piece(sq)
					print p.abbrev(),
			print "| " + str(r)
		print "-" * 23
		print "   ",
		for f in FILES:
			print f.upper(),


if __name__ == '__main__':
	board = Board.initial_position()
	board.dump()

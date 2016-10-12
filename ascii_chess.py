from abc import ABCMeta, abstractmethod

# TODO: The is_valid_move implementations does not take into account 
# positions where the King ends up in check.

WHITE = "white"
BLACK = "black"

FILES = [ 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h' ]
RANKS = [ 1, 2, 3, 4, 5, 6, 7, 8 ]


class InvalidMoveError(Exception):
	pass

class Square:

	def __init__(self, coordinate):
		file = coordinate[:1]
		if not file in FILES:
			err = "Not a valid file: '{}' (requires 'a' to 'h')".format(file)
			raise ValueError(err)
		rank = int(coordinate[1:].strip())
		if not rank in RANKS:
			err = "Not a valid rank: {} (requires 1 to 8)".format(rank)
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
		return "Square('{}{}')".format(self._file, self._rank)

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

	@abstractmethod
	def move_generator(self, board, start, to):
		pass

	def is_valid_move(self, board, start, to):
		"""Checks if suggested move is valid for this piece, on the given chess board. from and to
		are the current square and the destination square, respectively. Only non-capturing moves
		are considered, i.e. this method will return False if the target square is occupied by
		another piece."""
		if not board.is_empty(to):
			return False
		moves = self.move_generator(start, to)
		if moves is None:
			return False
		for sq in moves:
			if not board.is_empty(sq):
				return False
			if sq == to:
				return True
		return False

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
		if not board.is_empty(sq):
			return sq == target
	return False


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

	def is_valid_move(self, board, start, to):
		return self.is_covering_square(board, start, to) and board.is_empty(to)

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

	def is_valid_capture(self, board, start, to):
		return self.is_covering_square(board, start, to) and board.is_piece_of_opposite_color(to, self)

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

class Board:

	def __init__(self):
		self._squares = {}
		self._white_king = None
		self._black_king = None

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

	def remove_piece(self, s):
		"""Removes the piece from square s."""
		del self._squares[s]

	def is_empty(self, square):
		"""Checks if the given square is empty."""
		return square not in self._squares

	def is_piece_of_type_and_color(self, square, piece_type, color):
		"""Checks if there is a piece of the given type and color standing on the given square."""
		if self.is_empty(square):
			return False
		p = self.get_piece(square)
		return isinstance(p, piece_type) and p.get_color() == color

	def is_king(self, square, color):
		"""Checks if a King of the given color is standing on the given square."""
		return self.is_piece_of_type_and_color(square, King, color)

	def is_rook(self, square, color):
		"""Checks if a Rook of the given color is standing on the given square."""
		return self.is_piece_of_type_and_color(square, Rook, color)

	def is_pawn(self, square, color):
		"""Checks if a pawn of the given color is standing on the given square."""
		return self.is_piece_of_type_and_color(square, Pawn, color)

	def is_any_pawn(self, square):
		"""Checks if a pawn of any color is standing on the given square."""
		return not self.is_empty(square) and isinstance(self.get_piece(square), Pawn)

	def is_piece_of_opposite_color(self, square, piece):
		"""Checks if a piece of the opposite color than the given piece is standing on the given square."""
		return not self.is_empty(square) and not self.get_piece(square).is_same_color(piece)

	def collect_pieces_of_type_and_color(self, piece_type, color):
		"""Returns a list of the pieces of the given type and color currently on the board.
		Each entry in the returned list is a tuple: the first is the Square, the second the Piece."""
		return [i for i in self._squares.iteritems() if isinstance(i[1], piece_type) and i[1].get_color() == color]

	def clear_en_passant_squares(self):
		"""Clears the en-passant square for all pawns on the board."""
		for p in (i[1] for i in self._squares.iteritems() if isinstance(i[1], Pawn)):
			p.set_en_passant_square(None)

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
		self._white_king = Square('e1')
		self.add_piece(King(WHITE), self._white_king)
		self._black_king = Square('e8')
		self.add_piece(King(BLACK), self._black_king)

	def parse_move(self, input, expected_color, capture = False):
		# FIXME: This method is in dire need of refactoring!
		if input == "0-0" or input == "O-O":
			return Castling.king_side(expected_color)
		elif input == "0-0-0" or input == "O-O-O":
			return Castling.queen_side(expected_color)
		if " " in input:
			raise InvalidMoveError("Invalid move notation: " + input)
		if "-" in input:
			parts = input.split("-")
			f = Square(parts[0].strip())
			t = Square(parts[1].strip())
			return Move(f, t, False)
		elif "x" in input:
			return self.parse_capturing_move(input, expected_color)
		else:
			if len(input) == 2:
				# Input of type 'e4', i.e. a pawn move with only the target square given.
				# Treat this as 'Pe4', i.e. the same way we would a move like 'Nc3'.
				input = 'P' + input
			c = input[:1]
			if c in PIECE_TYPES:
				to_square = Square(input[1:])
				piece_type = PIECE_TYPES[c]
				pieces = self.collect_pieces_of_type_and_color(piece_type, expected_color)
				candidates = []
				for p in pieces:
					valid = p[1].is_valid_capture if capture else p[1].is_valid_move
					if valid(self, p[0], to_square):
						candidates.append(p)
				if len(candidates) == 0:
					raise InvalidMoveError("Invalid move. No {} {} can {} {}".format(
						expected_color, piece_type.__name__, "capture on" if capture else "move to", to_square))
				elif len(candidates) == 1:
					# The first [0] to get the single candidate, which is a tuple.
					# The second [0] to get the first item in the tuple, which is the Square.
					from_square = candidates[0][0]
					return Move(from_square, to_square, capture)
				else:
					# TODO: Add support for moves like 'Ngf4', and 'Ng2f4'.
					raise InvalidMoveError("Ambigous move. More than one {} {} can move to {}".format(
						expected_color, piece_type.__name__, to_square))
			else:
				if len(input) == 4:
					# Pawn move of the form 'e2e4'. We can handle it as 'e2-e4'
					return self.parse_move(input[:2] + "-" + input[2:], expected_color, False)
				else:
					raise InvalidMoveError("Invalid move notation: " + input)

	def parse_capturing_move(self, input, expected_color):
		"""Parses moves on the form 'Nxd5', 'fxe6', e4xd5'."""
		ind = input.index("x")
		move = None
		if ind == 1:
			if input[:1] in PIECE_TYPES:
				# 'Nxe5'. Can be handled as 'Ne5'.
				move = self.parse_move(input[:1] + input[2:], expected_color, True)
			else:
				# Pawn capture, e.g. 'fxe6'
				return self.parse_capturing_pawn_move(input, expected_color)
		elif ind == 2:
			# 'e4xd5'. Can be handled as 'e4-e5'.
			move = self.parse_move(input.replace("x", "-"), expected_color, True)
		if move is None:
			raise InvalidMoveError("Invalid move notation: " + input)
		if not move.is_capture(self):
			raise InvalidMoveError("Invalid move. Not a capture.")
		return move

	def parse_capturing_pawn_move(self, input, expected_color):
		"""Parses moves on the form 'fxe6', 'axb3'."""
		# TODO: Add support for en passant
		target_square = Square(input[2:])
		pawn_file = input[:1]
		pawn_rank = target_square.rank() - 1 if expected_color == WHITE else target_square.rank() + 1
		from_square = Square.fromFileAndRank(pawn_file, pawn_rank)
		if self.is_pawn(from_square, expected_color):
			pawn = self.get_piece(from_square)
			if pawn.is_valid_capture(self, from_square, target_square):
				return Move(from_square, target_square, True)
		raise InvalidMoveError("No {} pawn can capture on {}.".format(expected_color, target_square))

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
					print u'\u00b7', # a center dot
				else:
					p = self.get_piece(sq)
					print p.abbrev(),
			print "| " + str(r)
		print "-" * 23
		print "   ",
		for f in FILES:
			print f.upper(),


class Move:

	def __init__(self, from_square, to_square, capture):
		self._from = from_square
		self._to = to_square
		self._capture = capture

	def update_board(self, board, expected_color):
		piece = self.get_piece(board, expected_color)
		valid = piece.is_valid_capture if self._capture else piece.is_valid_move
		if not valid(board, self._from, self._to):
			raise ValueError("Illegal {}: {}".format("capture" if self._capture else "move", self))
		if self._capture:
			self.check_en_passant(board, piece)
		board.remove_piece(self._from)
		board.add_piece(piece, self._to)
		if not self._capture:
			self.update_en_passant_squares(board, piece)
		piece.set_has_moved()
		self.update_king_position(board, piece)

	def is_en_passant(self, board):
		# XXX: It would be nicer to use a sub-class for en-passant, just like we do for
		# castling. At the moment the parsing logic does not support that (easily) though.
		# For now we identify an en-passant move as a pawn move to an empty square of 
		# a neighboring file.
		return board.is_any_pawn(self._from) and board.is_empty(self._to) and (self._from.file() != self._to.file())

	def check_en_passant(self, board, piece):
		"""Checks if this move was an en-passant capture, in which case we must clear the square
		of the captured piece."""
		if self.is_en_passant(board):
			target_rank = self._to.rank() - 1 if piece.is_white() else self._to.rank() + 1
			target_square = Square.fromFileAndRank(self._to.file(), target_rank)
			board.remove_piece(target_square)

	def update_en_passant_squares(self, board, piece):
		"""Updates the en-passant property of all remaining pawns on the board, so that we can recognize
		an en-passant in the next move."""
		board.clear_en_passant_squares()
		if not isinstance(piece, Pawn):
			return
		if abs(self._to.rank() - self._from.rank()) != 2:
			return
		# At this point we know a pawn was moved two steps forward.
		# Pawns of the opposite color on each side of the target square
		# can now capture en-passant
		target_rank = self._to.rank() - 1 if piece.is_white() else self._to.rank() + 1
		target_square = Square.fromFileAndRank(self._to.file(), target_rank)
		sides = [f for f in (self._to.file() - 1, self._to.file() + 1) if (f >= 1 and f <= 8)]
		for f in sides:
			sq = Square.fromFileAndRank(f, self._to.rank())
			opposite_color = BLACK if piece.is_white() else WHITE
			if board.is_pawn(sq, opposite_color):
				p = board.get_piece(sq)
				p.set_en_passant_square(target_square)

	def update_king_position(self, board, piece):
		if isinstance(piece, King):
			if piece.is_white():
				board._white_king = self._to
			else:
				board._black_king = self._to

	def get_piece(self, board, expected_color):
		if board.is_empty(self._from):
			raise ValueError("Invalid move. No piece at " + str(self._from))
		p = board.get_piece(self._from)
		if not p.get_color() == expected_color:
			raise ValueError("Invalid move. The piece at " + str(self._from) + " is the wrong color.")
		return p

	def is_capture(self, board):
		if self.is_en_passant(board):
			return True
		if board.is_empty(self._from) or board.is_empty(self._to):
			return False
		p1 = board.get_piece(self._from)
		p2 = board.get_piece(self._to)
		return not p1.is_same_color(p2)

	def __str__(self):
		return str(self._from) + "-" + str(self._to)

	def __repr__(self):
		return "Move(Square('{}'), Square('{}'))".format(self._from, self._to)


class Castling(Move):

	@staticmethod
	def king_side(color):
		rank = 1 if color == WHITE else 8
		return Castling(Square.fromFileAndRank(5, rank), Square.fromFileAndRank(8, rank), False)

	@staticmethod
	def queen_side(color):
		rank = 1 if color == WHITE else 8
		return Castling(Square.fromFileAndRank(5, rank), Square.fromFileAndRank(1, rank), False)
	
	def update_board(self, board, expected_color):
		if board.is_king(self._from, expected_color):
			king = board.get_piece(self._from)
			if king.is_valid_move(board, self._from, self._to):
				rook = board.get_piece(self._to)
				new_king_file = 7 if self._to.file() == 8 else 3
				new_rook_file = 6 if new_king_file == 7 else 4
				rank = self._from.rank()
				board.add_piece(king, Square.fromFileAndRank(new_king_file, rank))
				board.add_piece(rook, Square.fromFileAndRank(new_rook_file, rank))
				board.remove_piece(self._from)
				board.remove_piece(self._to)
				king.set_has_moved()
				rook.set_has_moved()
				board.clear_en_passant_squares()
				self.update_king_position(board, king)
			else:
				raise InvalidMoveError("{} castling is not allowed for {}.".format(
					"King-side" if self._to.file() == 8 else "Queen-side", expected_color))
		else:
			raise InvalidMoveError("Illegal move. The {} King is not standing on {}.".format(expected_color, self._from))


class StopError(Exception):
	pass


class Game:

	def __init__(self):
		self._board = Board.initial_position()
		self._half_move = 1

	def loop(self):
		print
		self._board.dump()
		while True:
			try:
				input = raw_input("\nEnter a move ('q' to quit, 'b' to print board): ")
				self.handle_input(input)
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
					if len(file_name) == 0:
						return
					with open(file_name) as f:
						for line in (ln.strip() for ln in f if len(ln)):
							print line,
							if " " in line:
								moves = line.split(" ")
								self.handle_input(moves[0], False, False)
								self.handle_input(moves[1], False, False)
							else:
								self.handle_input(line, False, False)
					print '\n'
					self._board.dump()
			else:
				expected_color = WHITE if (self._half_move % 2) else BLACK
				move = self._board.parse_move(input, expected_color)
				move.update_board(self._board, expected_color)
				self._half_move += 1
				if print_board:
					self._board.dump()


if __name__ == '__main__':
	game = Game()
	game.loop()

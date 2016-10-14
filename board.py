from common import *
from piece import *
from move import *


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

	def save_state(self):
		return (self._squares.copy(), self._white_king, self._black_king)

	def restore_state(self, state):
		self._squares = state[0].copy()
		self._white_king = state[1]
		self._black_king = state[2]

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

	def is_king_in_check(self, color):
		square = self._white_king if color == WHITE else self._black_king
		if square is None:
			return False
		for i in self._squares.iteritems():
			piece = i[1]
			if piece.get_color() != color and piece.is_covering_square(self, i[0], square):
				return True
		return False

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
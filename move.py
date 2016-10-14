from common import *
from piece import *

class Move:

	def __init__(self, from_square, to_square, capture):
		self._from = from_square
		self._to = to_square
		self._capture = capture

	def update_board(self, board, expected_color):
		state = board.save_state()
		piece = self.get_piece(board, expected_color)
		valid = piece.is_valid_capture if self._capture else piece.is_valid_move
		if not valid(board, self._from, self._to):
			raise ValueError("Illegal {}: {}".format("capture" if self._capture else "move", self))
		if self._capture:
			self.check_en_passant(board, piece)
		board.remove_piece(self._from)
		board.add_piece(piece, self._to)
		self.update_king_position(board, piece)
		if board.is_king_in_check(expected_color):
			board.restore_state(state)
			raise InvalidMoveError("Invalid move: {}'s King is in check.".format(expected_color))
		if not self._capture:
			self.update_en_passant_squares(board, piece)
		piece.set_has_moved()

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
				if board.is_king_in_check(expected_color):
					raise InvalidMoveError("Castling is not allowed since the King is in check")
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
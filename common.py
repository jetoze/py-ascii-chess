
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
		
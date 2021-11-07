import sys
import re
import math

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

global mesh
mesh = None

fatorEscala = 1.05
fatorRotacao = 0.05
fatorTranslacao = 0.05

####################################################################
# Objeto Mesh, com vertices e faces

class Vertex(object):
	def __init__(self):
		self._x = 0.0
		self._y = 0.0
		self._z = 0.0
		self._nx = 0.0
		self._ny = 0.0
		self._nz = 0.0
		self._s = 0.0
		self._t = 0.0
		self._hasCoords = False
		self._hasNormals = False
		self._hasST = False
	def setX(self, x):
		self._hasCoords = True
		self._x = x
	def setY(self, y):
		self._hasCoords = True
		self._y = y
	def setZ(self, z):
		self._hasCoords = True
		self._z = z
	def coords(self):
		return (self._x, self._y, self._z)
	def setNX(self, nx):
		self._hasNormal = True
		self._nx = nx
	def setNY(self, ny):
		self._hasNormal = True
		self._ny = ny
	def setNZ(self, nz):
		self._hasNormal = True
		self._nz = nz
	def normal(self):
		return (self._nx, self._ny, self._nz)
	def setS(self, s):
		self._hasST = True
		self._s = s
	def setT(self, t):
		self._hasST = True
		self._t = t
	def stcoords(self):
		return (self._s, self._t)
	def hasCoords(self):
		return self._hasCoords
	def hasNormal(self):
		return self._hasNormal
	def hasST(self):
		return self._hasST
		
class Face(object):
	def __init__(self):
		self._vertices = []
	def set(self, l):
		self._vertices = l
	def vertices(self):
		return self._vertices
		
class Mesh(object):
	def __init__(self):
		self.vertices = []
		self.faces = []
	def addVertex(self, v):
		self.vertices.append(v)
	def getVertex(self, vi):
		return self.vertices[vi]
	def addFace(self, f):
		self.faces.append(f)
	def draw(self):
		mode = None
		for face in self.faces:
			numvertices = len(face.vertices())
			if numvertices == 3 and mode != GL_TRIANGLES:
				if mode:
					glEnd()
				glBegin(GL_TRIANGLES)
				mode = GL_TRIANGLES
			elif numvertices == 4 and mode != GL_QUADS:
				if mode:
					glEnd()
				glBegin(GL_QUADS)
				mode = GL_QUADS
			elif numvertices > 4:
				if mode:
					glEnd()
				glBegin(GL_POLYGON)
				mode = GL_POLYGON
			elif numvertices < 3:
				raise RuntimeError('A face tem menos de 3 vertices')
			for vertex in [self.getVertex(i) for i in face.vertices()]:
				if vertex.hasNormal():
					glNormal3f(*(vertex.normal()))
				glVertex3f(*(vertex.coords()))
			if mode == GL_POLYGON:
				glEnd()
				mode = None
		if mode:
			glEnd()

####################################################################
# matrizes de transformacoes

def equals(a, b):
    DELTA = .001
    if(abs(a-b) < DELTA):
        return True
    return False

class Vector4d:
    def __init__(self, x, y, z, w):
        self.val = [x, y, z, w]

    def __getitem__(self, i):
        return self.val[i]

    def __str__(self):
        return "<%7.3f, %7.3f, %7.3f, %7.3f>" % (self[0], self[1], self[2], self[3])

    def __setitem__(self, i, x):
        self.val[i] = x

    def list(self):
        return self.val

    def magnitude(self):
        return math.sqrt(self[0]*self[0] + self[1]*self[1] + self[2]*self[2] + self[3]*self[3])

    def scale(self, factor):
        for i in range(4):
            self.val[i] = self.val[i]*factor

    def makeUnit(self):
        if not self.isZero():
            m = self.magnitude()
            for i in range(4):
                self.val[i] /= m

    def isZero(self):
        for i in range(4):
            if not equals(self.val[i], 0.0):
                return False
        return True

    def __mul__(self, m):
        m = m.transpose()
        return Vector4d(*[dot(m[i], self) for i in range(4)])

    def __add__(self, v):
        return Vector4d(*[self[i] + v[i] for i in range(4)])

    def __iadd__(self, v):
        for i in range(4):
            self[i] += v[i]
        return self

    def __sub__(self, v):
        return Vector4d(*[self[i] - v[i] for i in range(4)])

    def __isub__(self, v):
        for i in range(4):
            self[i] -= v[i]
        return self

    def __eq__(self, v):
        for i in range(4):
            if not equals(self[i], v[i]):
                return False
        return True

    def __ne__(self, v):
        return not (self == v)

    def __len__(self):
        return 4

def dot(u, v):
    if len(u) != len(v):
        raise RuntimeError('Os vetores nao tem a mesma dimensao')
    return sum([u[i]*v[i] for i in range(len(u))])

def proj(u, v):
    return v.scale(dot(u, v)/dot(v, v))

class Matrix4x4:
    def __init__(self, *args):
        if len(args) == 4:
            self._createFromColumns(*args)
        if len(args) == 16:
            self._createFromElements(*args)

    def _createFromElements(self, a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p):
        self.val = [Vector4d(a, e, i, m),
                    Vector4d(b, f, j, n),
                    Vector4d(c, g, k, o),
                    Vector4d(d, h, l, p)]

    def _createFromColumns(self, a, b, c, d):
        self.val = [a, b, c, d]

    def __getitem__(self, i):
        return self.val[i]

    def __setitem__(self, i, x):
        self.val[i] = x

    def __str__(self):
        s = ""
        for i in range(4):
            s += "|%7.3f, %7.3f, %7.3f, %7.3f|\n" % (self[0][i],
                                                     self[1][i],
                                                     self[2][i],
                                                     self[3][i])
        return s

    def __eq__(self, m):
        for i in range(4):
            if self[i] != m[i]:
                return False
        return True

    def __ne__(self, m):
        return not (self == m)

    def scale(self, s):
        for i in range(4):
            self[i].scale(s)

    def transpose(self):
        return Matrix4x4(*[self[i][j]
                           for i in range(4) for j in range(4)])

    def copy(self):
        return Matrix4x4(*[self[j][i]
                           for i in range(4) for j in range(4)])

    # def det(self):
        # return ( self[0][0]*self[1][1]*self[2][2] -
        # self[0][0]*self[1][2]*self[2][1] +
        # self[1][0]*self[0][1]*self[2][2] -
        # self[1][0]*self[0][2]*self[2][1] +
        # self[2][0]*self[0][1]*self[1][2] -
        # self[2][0]*self[0][2]*self[1][1] )

    def __mul__(self, n):
        m = self.transpose()
        return Matrix4x4(*[dot(m[i], n[j])
                           for i in range(4) for j in range(4)])

    def orthogonalize(self):
        m = self.copy()
        for i in range(4):
            for j in range(i):
                m[i] -= proj(m[i], m[j])
        return m

    def orthonormalize(self):
        m = self.orthogonalize()
        for i in range(4):
            m[i].makeUnit()
        return m

    def isOrthogonal(self):
        return (self * self.transpose()) == getIdentity4x4()

def getIdentity4x4():
    return Matrix4x4(1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1)

def rotateX(theta):
    s = math.sin(theta)
    c = math.cos(theta)
    return Matrix4x4(1, 0, 0, 0,
                     0, c, -s, 0,
                     0, s, c, 0,
                     0, 0, 0, 1)

def rotateY(theta):
    s = math.sin(theta)
    c = math.cos(theta)
    return Matrix4x4(c, 0, s, 0,
                     0, 1, 0, 0,
                     -s, 0, c, 0,
                     0, 0, 0, 1)

def rotateZ(theta):
    s = math.sin(theta)
    c = math.cos(theta)
    return Matrix4x4(c, -s, 0, 0,
                     s, c, 0, 0,
                     0, 0, 1, 0,
                     0, 0, 0, 1)

def translate(x, y, z):
    return Matrix4x4(1, 0, 0, x,
                     0, 1, 0, y,
                     0, 0, 1, z,
                     0, 0, 0, 1)

def scale(x, y, z):
    return Matrix4x4(x, 0, 0, 0,
                     0, y, 0, 0,
                     0, 0, z, 0,
                     0, 0, 0, 1)


def printBreak():
    print("-------------------")

####################################################################
# Objeto .ply, que esta em um arquivo qualquer .ply
 
def get_float(str):
	return float(str)

def get_double(str):
	return float(str)

def get_char(str):
	return int(str)

def get_uchar(str):
	return int(str)

def get_short(str):
	return int(str)

def get_ushort(str):
	return int(str)

def get_int(str):
	return int(str)

def get_uint(str):
	return int(str)	

def parse_ply(fname):
	m = Mesh()
	state = 'init'
	format_re = re.compile('format\\s+ascii\\s+1.0')
	comment_re = re.compile('comment\\s.*')
	element_re = re.compile('element\\s+(?P<name>\\w+)\\s+(?P<num>\\d+)')
	property_re = re.compile('property\\s+(?P<type>\\w+)\\s+(?P<name>\\w+)')
	property_list_re = re.compile('property\\s+list\\s+(?P<itype>\\w+)\\s+(?P<etype>\\w+)\\s+(?P<name>\\w+)')
	element_types = []
	vertex_names = {
		'x': lambda v, x: v.setX(x),
		'y': lambda v, y: v.setY(y),
		'z': lambda v, z: v.setZ(z),
		'nx': lambda v, nx: v.setNX(nx),
		'ny': lambda v, ny: v.setNY(ny),
		'nz': lambda v, nz: v.setNZ(nz),
		's': lambda v, s: v.setS(s),
		't': lambda v, t: v.setT(t)
	}
	face_names = {
		#'vertex_indices': (lambda f, l, m=m: f.set([m.getVertex(v) for v in l])) # Para valores reais de vertices
		'vertex_indices': (lambda f, l, m=m: f.set(l))                            # Para referencias de vertices
	}
	element_type_dict = {
		'vertex' : (lambda: Vertex(), vertex_names, lambda v, m=m: m.addVertex(v)),
		'face' : (lambda: Face(), face_names, lambda f, m=m: m.addFace(f))
	}
	type_handles = {
		'float' : get_float,
		'double' : get_double,
		'char' : get_char,
		'uchar' : get_uchar,
		'short' : get_short,
		'ushort' : get_ushort,
		'int' : get_int,
		'uint' : get_uint
	}
	i = 0
	j = 0
	for line in open(fname, 'r'):
		line = line.rstrip()
		if state == 'init':
			if line != 'ply':
				raise RuntimeError('Arquivo .PLY: arquivo nao eh do formato .ply')
			state = 'format'
		elif state == 'format':
			if not format_re.match(line):
				raise RuntimeError('Arquivo .PLY: formato de arquivo ply não suportado')
			state = 'header'
		elif state == 'header':
			if comment_re.match(line):
				continue
			match = element_re.match(line)
			if match:
				element_types.append((match.group('name'), int(match.group('num')), []))
				continue
			match = property_list_re.match(line)
			if match:
				element_types[-1][2].append((match.group('name'), 'list', match.group('itype'), match.group('etype')))
				continue
			match = property_re.match(line)
			if match:
				element_types[-1][2].append((match.group('name'), match.group('type')))
				continue
			if line == 'end_header':
				state = 'body'
				continue
			raise RuntimeError('Arquivo .PLY: cabecalho desconhecido')
		elif state == 'body':
			if j >= element_types[i][1]:
				j = 0
				i = i + 1
			if i >= len(element_types):
				raise RuntimeExeception('Arquivo .PLY: muitos dados no arquivo')
			line = line.split()
			actions = element_type_dict[element_types[i][0]]
			obj = actions[0]()
			for property in element_types[i][2]:
				x = None
				if property[1] == 'list':
					numelems = type_handles[property[2]](line[0])
					line = line[1:]
					x = []
					for count in range(numelems):
						x.append(type_handles[property[3]](line[0]))
						line = line[1:]
				else:
					x = type_handles[property[1]](line[0])
					line = line[1:]
				actions[1][property[0]](obj, x)
			actions[2](obj)
			j = j + 1
	return m

####################################################################
# Funcoes doIdle(), doKeyboard(), doSpecial(), que sao chamadas pelo glutMainLoop(), ininterruptamente

def doIdle():    
	pass
	
def doKeyboard(*args):
	global cameraMatrix
	if args[0] == b'+':
		cameraMatrix = cameraMatrix * scale(1/fatorEscala, 1/fatorEscala, 1/fatorEscala)
	elif args[0] == b'-':
		cameraMatrix = cameraMatrix * scale(fatorEscala, fatorEscala, fatorEscala)
	else:
		return
	doRedraw()
	
def doSpecial(*args):
	global cameraMatrix
	if glutGetModifiers() & GLUT_ACTIVE_SHIFT:
		if args[0] == GLUT_KEY_UP:
			cameraMatrix = cameraMatrix * translate(0, -fatorTranslacao, 0) # Seta para cima
		if args[0] == GLUT_KEY_DOWN:
			cameraMatrix = cameraMatrix * translate(0, fatorTranslacao, 0) # Seta para baixo
		if args[0] == GLUT_KEY_LEFT:
			cameraMatrix = cameraMatrix * translate(fatorTranslacao, 0, 0) # Seta para esquerda
		if args[0] == GLUT_KEY_RIGHT:
			cameraMatrix = cameraMatrix * translate(-fatorTranslacao, 0, 0) # Seta para direita
	else:
		if args[0] == GLUT_KEY_UP:
			cameraMatrix = cameraMatrix * rotateX(-fatorRotacao) # Seta para cima
		if args[0] == GLUT_KEY_DOWN:
			cameraMatrix = cameraMatrix * rotateX(fatorRotacao) # Seta para baixo
		if args[0] == GLUT_KEY_LEFT:
			cameraMatrix = cameraMatrix * rotateY(-fatorRotacao) # Seta para esquerda
		if args[0] == GLUT_KEY_RIGHT:
			cameraMatrix = cameraMatrix * rotateY(fatorRotacao) # Seta para direita
	doRedraw()

####################################################################
# Funcao chamada pelo glutMainLoop(), quando a janela eh redimensionada

def doReshape(width, height):
	global cameraMatrix
	glMatrixMode(GL_PROJECTION)
	glLoadIdentity()
	glViewport(0,0,width,height)
	gluPerspective(45.0, ((float)(width))/height, .1, 200)
	doCamera()

def doCamera():
	glMatrixMode(GL_MODELVIEW)
	glLoadIdentity()
	orientationMatrix = cameraMatrix.copy()
	orientationMatrix[3] = Vector4d(0, 0, 0, 1)
	pos = Vector4d(0, 3, 10, 1) * cameraMatrix
	lookAt = Vector4d(0, 0, 0, 1) * cameraMatrix
	direction = Vector4d(0, 1, 0, 1) * orientationMatrix
	gluLookAt(*(pos.list()[:-1] + lookAt.list()[:-1] + direction.list()[:-1]))

####################################################################
# Funcao chamada pelo glutMainLoop(), quando a tela precisa ser redesenhada
def doRedraw():
	doCamera()
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
	glMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, (.25, .25, .25, 1.0))
	glMaterial(GL_FRONT_AND_BACK, GL_SPECULAR, (1.0, 1.0, 1.0, .5))
	glMaterial(GL_FRONT_AND_BACK, GL_SHININESS, (128.0, ))
	glMatrixMode(GL_MODELVIEW)
	mesh.draw()
	glutSwapBuffers()  # Desenha a imagem na tela se tiver buffers duplos

####################################################################
# Programa principal

if __name__ == '__main__':
	global cameraMatrix
	cameraMatrix = getIdentity4x4()
	mesh = parse_ply(sys.argv[1]) 
	
	# Inicialização basica
	glutInit([])
	glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)
	glutInitWindowSize(640,480)
	glutCreateWindow("Renderizador de arquivos '.ply', para Open GL")
	glEnable(GL_DEPTH_TEST)      # Poligonos mais longes sao renderizados primeiro
	glEnable(GL_NORMALIZE)       # Impede que a escala altere as cores
	glClearColor(0., 0., 0., 0.0) # Cor de fundo da tela

	# Estabelecendo 2 pontos de luzes
	glEnable(GL_LIGHTING)
	BRIGHT4f = (1.0, 1.0, 1.0, 1.0)  # Cor para luz brilhante
	DIM4f = (.2, .2, .2, 1.0)        # Cor para luz fraca
	glLightfv(GL_LIGHT0, GL_AMBIENT, BRIGHT4f)
	glLightfv(GL_LIGHT0, GL_DIFFUSE, BRIGHT4f)
	glLightfv(GL_LIGHT0, GL_POSITION, (10, 10, 10, 0))
	glEnable(GL_LIGHT0)
	glLightfv(GL_LIGHT1, GL_AMBIENT, DIM4f)
	glLightfv(GL_LIGHT1, GL_DIFFUSE, DIM4f)
	glLightfv(GL_LIGHT1, GL_POSITION, (-10, 10, -10, 0))
	glEnable(GL_LIGHT1)

	# Funcoes chamadas em loops
	glutDisplayFunc(doRedraw)        # Executado quando a tela precisa ser redesenhada
	glutIdleFunc(doIdle)             # Executado num loop quando a tela nao eh redesenhada
	glutReshapeFunc(doReshape)       # Executado quando a tela é redimensionada
	glutSpecialFunc(doSpecial)       # Executado quando as teclas Setas sao pressionadas
	glutKeyboardFunc(doKeyboard)     # Executado quando qualquer tecla eh pressionada

	# Executa a interface ininterruptamente, chamando as funcoes doRedraw(), doIdle(), doReshape()
	glutMainLoop()
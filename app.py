# app.py
# Archivo principal de la aplicación Flask.
# Contiene la clase PaginaWeb que encapsula la app, la conexión a la DB y todas las rutas.

from flask import Flask, render_template, request, session, redirect, url_for, jsonify
# Importa las herramientas de Flask que se usan:
# - Flask: para crear la app
# - render_template: para renderizar archivos HTML (Jinja2)
# - request: para acceder a datos de peticiones (form, args, headers)
# - session: para almacenar datos por usuario (carrito, usuario logueado)
# - redirect / url_for: para redireccionamientos
# - jsonify: para responder JSON en endpoints AJAX

import mysql.connector
# Conector para MySQL (permite conectar y ejecutar queries)

class PaginaWeb:
    # Clase que agrupa la aplicación, la conexión a la DB y la configuración de rutas.
    def __init__(self, nombre):
        # Constructor: crea la app Flask y configura la base de datos.
        self.app = Flask(nombre)
        # Clave secreta para sesiones (cookies firmadas). En producción debe venir de variable de entorno.
        self.app.secret_key = "superclave"

        # 🔹 CONEXIÓN A MYSQL (AGREGADO)
        # Se establece la conexión a la base de datos MySQL.
        # ⚠️ Atención: aquí la contraseña está vacía. En producción debes usar credenciales seguras y variables de entorno.
        self.db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",  # si tu MySQL tiene contraseña, agrégala aquí
            database="postres"
        )
        # Cursor con dictionary=True para recibir cada fila como dict {columna: valor}
        self.cursor = self.db.cursor(dictionary=True)

        # Configura las rutas de la aplicación
        self.configurar_rutas()

    def configurar_rutas(self):
        # Método que define todas las rutas (endpoints) de la app.
        # Las rutas usan self.app.route para que queden registradas en la instancia Flask.

        # --------------------------
        # 🔹 LOGIN POST (AGREGADO)
        # --------------------------
        @self.app.route("/login", methods=["POST"])
        def login_post():
            # Ruta que procesa el formulario de login (método POST).
            # Se espera recibir 'usuario' y 'password' en request.form.

            usuario = request.form.get("usuario")
            # Se intenta convertir el usuario a entero (en tu DB parece que Id_Usuario es numérico)
            try:
                usuario = int(usuario)  # convierte la cadena a número
            except:
                # Si no es convertible, renderiza el login con un mensaje de error.
                # Nota: devolver render_template aquí evita un crash por valor inválido.
                return render_template("login.html", error="Usuario inválido")

            password = request.form.get("password")
            # Query parametrizada para evitar SQL injection.
            query = """
                SELECT * FROM usuario 
                WHERE Id_Usuario=%s AND Contraseña=%s 
            """
            # Ejecuta la query usando parámetros (usuario, password)
            self.cursor.execute(query, (usuario, password))
            datos = self.cursor.fetchone()  # trae la primera fila que cumpla la condición

            if datos:
                # Si se encontró el usuario -> crea sesión y redirige a la página de bienvenida.
                session["usuario"] = datos["Nombre"]
                return redirect(url_for("bienvenido"))
            else:
                # Si no se encontró, vuelve a la página de login con error.
                return render_template("login.html", error="Usuario o contraseña incorrectos")

        # --------------------------
        # 🔹 Página de Bienvenida
        # --------------------------
        @self.app.route("/bienvenido")
        def bienvenido():
            # Muestra la página de bienvenida. Intenta obtener el nombre desde sesión.
            nombre = session.get("usuario", "Usuario")
            return render_template("bienvenido.html", nombre=nombre)

        # --------------------------
        # 🔹 AQUI EMPIEZA TU CÓDIGO ORIGINAL
        # --------------------------

        @self.app.route("/agregar_carrito", methods=["POST"])
        def agregar_carrito():
            # Añade un producto al carrito almacenado en session.
            # Los datos llegan por form: titulo, precio, imagen. Se fija cantidad inicial = 1.

            producto = {
                "titulo": request.form.get("titulo"),
                "precio": float(request.form.get("precio") or 0),
                "imagen": request.form.get("imagen"),
                "cantidad": 1
            }

            # Si la sesión no tiene carrito, se crea uno vacío (lista).
            if "carrito" not in session:
                session["carrito"] = []

            existe = False
            # Busca si el producto ya está en el carrito; si está, incrementa cantidad.
            for item in session["carrito"]:
                if item["titulo"] == producto["titulo"]:
                    item["cantidad"] += 1
                    existe = True
                    break

            # Si no existe, lo añade a la lista del carrito.
            if not existe:
                session["carrito"].append(producto)

            # Indica que la sesión fue modificada (para que Flask lo persista)
            session.modified = True
            return "OK"  # Respuesta simple para AJAX

        @self.app.route("/carrito")
        def carrito():
            # Renderiza la vista del carrito mostrando el contenido de la sesión.
            carrito = session.get("carrito", [])
            return render_template("carrito.html", carrito=carrito)

        @self.app.route("/eliminar_item/<titulo>")
        def eliminar_item(titulo):
            # Elimina un ítem del carrito filtrando por título.
            carrito = session.get("carrito", [])
            carrito = [item for item in carrito if item["titulo"] != titulo]
            session["carrito"] = carrito
            session.modified = True
            return redirect(url_for("carrito"))

        @self.app.route("/actualizar_cantidad", methods=["POST"])
        def actualizar_cantidad():
            # Endpoint que actualiza la cantidad de un producto dentro del carrito.
            # Espera 'titulo' y 'accion' en request.form (accion: 'sumar' o 'restar').

            titulo = request.form.get("titulo")
            accion = request.form.get("accion")

            carrito = session.get("carrito", [])

            removed = False    # Indica si el item fue removido (cantidad <= 0)
            nueva_cantidad = None

            # Recorre el carrito para encontrar el item y ajustar cantidad
            for item in carrito:
                if item["titulo"] == titulo:
                    if accion == "sumar":
                        item["cantidad"] = int(item.get("cantidad", 0)) + 1
                    elif accion == "restar":
                        item["cantidad"] = int(item.get("cantidad", 0)) - 1

                    # Si la cantidad queda en 0 o menos, se elimina el item
                    if item["cantidad"] <= 0:
                        carrito = [i for i in carrito if i["titulo"] != titulo]
                        removed = True
                        nueva_cantidad = 0
                    else:
                        nueva_cantidad = item["cantidad"]
                    break  # sale del loop cuando ya actualizó el item

            # Guarda cambios en session
            session["carrito"] = carrito
            session.modified = True

            # Responde en JSON si la petición viene por AJAX (X-Requested-With) o si es JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return jsonify({"ok": True, "cantidad": nueva_cantidad or 0, "removed": removed})

            # Si no es AJAX, redirige a la vista del carrito
            return redirect(url_for("carrito"))

        @self.app.route("/")
        def index():
            # Ruta raíz -> renderiza index.html
            return render_template("index.html")

        @self.app.route('/nosotros')
        def nosotros():
            # Muestra la página 'Nosotros'
            return render_template('nosotros.html')

        @self.app.route("/contacto", methods=["GET", "POST"])
        def contacto():
            # Página de contacto. Si es POST, recoge los datos del formulario
            mensaje_enviado = False
            if request.method == "POST":
                nombre = request.form.get("nombre")
                correo = request.form.get("correo")
                telefono = request.form.get("telefono")
                mensaje = request.form.get("mensaje")
                # Aquí solo cambias mensaje_enviado a True para mostrar notificación en template.
                # ⚠️ Si quieres guardar mensajes, aquí deberías insertar en la DB.
                mensaje_enviado = True
            return render_template("contacto.html", mensaje_enviado=mensaje_enviado)

        @self.app.route('/login')
        def login():
            # Muestra la página de login (GET)
            return render_template('login.html')

        @self.app.route('/producto')
        def producto():
            # Consulta todos los productos desde la tabla producto y los envía al template.
            query = "SELECT * FROM producto"
            self.cursor.execute(query)
            productos = self.cursor.fetchall()  # devuelve lista de diccionarios
            return render_template("producto.html", productos=productos)

        @self.app.route('/producto_detalle')
        def producto_detalle():
            # Página de detalle de producto que recibe datos por query params.
            titulo = request.args.get("titulo", "Sin título")
            descripcion = request.args.get("descripcion", "Sin descripción")
            imagen = request.args.get("imagen", "")
            precio = request.args.get("precio")
            return render_template("producto_detalle.html",
                titulo=titulo,
                descripcion=descripcion,
                imagen=imagen,
                precio=precio)

        @self.app.route("/vaciar_carrito", methods=["POST"])
        def vaciar_carrito():
            # Vacía el carrito de la sesión (usado después de finalizar compra).
            session["carrito"] = []
            session.modified = True
            return jsonify({"ok": True})

        @self.app.route("/gestion_productos")
        def gestion_productos():
            # Vista para administrar productos (listar)
            query = "SELECT * FROM producto"
            self.cursor.execute(query)
            productos = self.cursor.fetchall()
            return render_template("gestion_productos.html", productos=productos)

        @self.app.route("/producto/agregar", methods=["GET","POST"])
        def agregar_producto():
            # GET -> muestra formulario; POST -> inserta producto en la DB
            if request.method == "GET":
                 return render_template("agregar_producto.html")
            
            # Si es POST, obtiene los campos del formulario
            nombre = request.form["nombre"]
            descripcion = request.form["descripcion"]
            imagen = request.form["imagen"]
            precio = request.form["precio"]
            stock = request.form["stock"]
            fecha = request.form["fecha"]

            # Query parametrizada para insertar un nuevo producto.
            query = """
                INSERT INTO producto 
                (Nombre_Producto, Descripcion, Imagen, Precio, Stock, Fecha_Vencimiento, Usuario_D_Creacion, Fecha_Hora_Creacion)
                VALUES (%s, %s, %s, %s, %s, %s, 'admin', NOW())
            """

            valores = (nombre, descripcion, imagen, precio, stock, fecha)

            self.cursor.execute(query, valores)
            # Confirma la transacción en la DB
            self.db.commit()

            # Redirige a la vista de gestión de productos
            return redirect("/gestion_productos")
        
        @self.app.route("/producto/editar/<int:id>", methods=["GET", "POST"])
        def editar_producto(id):
            # Editar producto por id
            if request.method == "GET":
                # GET -> cargar datos actuales del producto y mostrarlos en el formulario
                self.cursor.execute("SELECT * FROM producto WHERE Id_Producto=%s", (id,))
                producto = self.cursor.fetchone()
                return render_template("editar_producto.html", producto=producto)

            # Si es POST → guardar cambios enviados desde el formulario
            nombre = request.form["nombre"]
            descripcion = request.form["descripcion"]
            imagen = request.form["imagen"]
            precio = request.form["precio"]
            stock = request.form["stock"]
            fecha = request.form["fecha"]

            # Query para actualizar el producto
            query = """
                UPDATE producto SET 
                    Nombre_Producto=%s,
                    Descripcion=%s,
                    Imagen=%s,
                    Precio=%s,
                    Stock=%s,
                    Fecha_Vencimiento=%s
                WHERE Id_Producto=%s
            """

            valores = (nombre, descripcion, imagen, precio, stock, fecha, id)

            self.cursor.execute(query, valores)
            self.db.commit()

            return redirect("/gestion_productos")
        
        @self.app.route("/producto/eliminar/<int:id>")
        def eliminar_producto(id):
            # Elimina un producto por id
            query = "DELETE FROM producto WHERE Id_Producto=%s"
            self.cursor.execute(query, (id,))
            self.db.commit()
            return redirect("/gestion_productos")
        
        # --------------------------
        # 🔹 Gestión de Proveedores
        # --------------------------
        @self.app.route("/proveedor")
        def proveedor():
            # Lista todos los proveedores
            self.cursor.execute("SELECT * FROM proveedor")
            proveedores = self.cursor.fetchall()
            return render_template("proveedor.html", proveedores=proveedores)

        @self.app.route("/proveedor/agregar", methods=["GET","POST"])
        def proveedor_agregar():
            # GET -> muestra formulario; POST -> inserta proveedor
            if request.method == "GET":
                 return render_template("agregar_proveedor.html")
            nombre = request.form["nombre"]
            telefono = request.form["telefono"]
            correo = request.form["correo"]
            direccion = request.form["direccion"]
            tipo = request.form["tipo"]

            query = """
                INSERT INTO proveedor (Nombre, Telefono, Correo, Direccion, Tipo_Producto, Usuario_D_Creacion, Fecha_Hora_Creacion)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """
            usuario = session.get("usuario", "admin")

            # Ejecuta el insert con el usuario que realiza la acción
            self.cursor.execute(query, (nombre, telefono, correo, direccion, tipo, usuario))
            self.db.commit()

            return redirect("/proveedor")
        
        @self.app.route("/proveedor/editar/<int:id>", methods=["GET", "POST"])
        def proveedor_editar(id):
            # GET → mostrar formulario con datos existentes
            if request.method == "GET":
                self.cursor.execute("SELECT * FROM proveedor WHERE Id_Proveedor=%s", (id,))
                proveedor = self.cursor.fetchone()
                return render_template("editar_proveedor.html", proveedor=proveedor)

            # POST → actualizar datos del proveedor
            nombre = request.form["nombre"]
            telefono = request.form["telefono"]
            correo = request.form["correo"]
            direccion = request.form["direccion"]
            tipo = request.form["tipo"]

            query = """
                UPDATE proveedor SET 
                    Nombre=%s, 
                    Telefono=%s, 
                    Correo=%s, 
                    Direccion=%s, 
                    Tipo_Producto=%s
                WHERE Id_Proveedor=%s
            """

            self.cursor.execute(query, (nombre, telefono, correo, direccion, tipo, id))
            self.db.commit()

            return redirect("/proveedor")

        @self.app.route("/proveedor/eliminar/<int:id>")
        def proveedor_eliminar(id):
            # Borra un proveedor por id
            self.cursor.execute("DELETE FROM proveedor WHERE Id_Proveedor=%s", (id,))
            self.db.commit()
            return redirect("/proveedor")
        
        @self.app.route("/guardar_compra", methods=["POST"])
        def guardar_compra():
            # Endpoint que almacena una compra completa (comprador, venta, detalle) en la BD.
            nombre = request.form.get("nombre")
            correo = request.form.get("correo")
            telefono = request.form.get("telefono")
            direccion = request.form.get("direccion")

            # Usuario actual que realiza la compra (por defecto 'admin' si no hay sesión)
            usuario = session.get("usuario", "admin")
            carrito = session.get("carrito", [])

            # -------------------------------
            # 1️⃣ GUARDAR COMPRADOR
            # -------------------------------
            query_comprador = """
                INSERT INTO comprador (Nombre, Correo, Telefono, Direccion, Usuario_D_Creacion, Fecha_Hora_Creacion)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """
            valores = (nombre, correo, telefono, direccion, usuario)

            # Inserta comprador y hace commit
            self.cursor.execute(query_comprador, valores)
            self.db.commit()

            # id_comprador: id auto-increment generado por MySQL para la fila recién insertada
            id_comprador = self.cursor.lastrowid   # ← AQUÍ USAMOS OPCIÓN 1

            # -------------------------------
            # 2️⃣ CALCULAR TOTAL DE LA VENTA
            # -------------------------------
            # Suma (precio * cantidad) para cada ítem en el carrito
            total = sum(item["precio"] * item["cantidad"] for item in carrito)

            # -------------------------------
            # 3️⃣ GUARDAR VENTA
            # -------------------------------
            query_venta = """
                INSERT INTO venta (Id_Comprador, Fecha_Venta, Total, Usuario_D_Creacion, Fecha_Hora_Creacion)
                VALUES (%s, CURDATE(), %s, %s, NOW())
            """
            self.cursor.execute(query_venta, (id_comprador, total, usuario))
            self.db.commit()

            # id_venta: id de la venta recién creada
            id_venta = self.cursor.lastrowid   # ← ID DE LA VENTA

            # -------------------------------
            # 4️⃣ GUARDAR DETALLE DE LA VENTA
            # -------------------------------
            for item in carrito:
                subtotal = item["precio"] * item["cantidad"]

                # Inserta una fila en venta_detalle.
                # Nota: Id_Producto se busca por nombre con una subconsulta (LIMIT 1).
                query_detalle = """
                    INSERT INTO venta_detalle 
                    (Id_Venta, Id_Producto, Cantidad, Precio_Unitario, Subtotal, Usuario_D_Creacion, Fecha_Hora_Creacion)
                    VALUES (%s, 
                            (SELECT Id_Producto FROM producto WHERE Nombre_Producto = %s LIMIT 1), 
                            %s, %s, %s, %s, NOW())
                """

                # Ejecuta la inserción del detalle con los valores correspondientes
                self.cursor.execute(query_detalle, (
                    id_venta,
                    item["titulo"],
                    item["cantidad"],
                    item["precio"],
                    subtotal,
                    usuario
                ))

            # Finalmente confirma todas las inserciones del detalle
            self.db.commit()

            # limpiar carrito de la sesión una vez guardada la compra
            session["carrito"] = []
            session.modified = True

            return redirect("/compra_realizada")

        
        @self.app.route("/compra_realizada")
        def compra_realizada():
            # Muestra la vista final de compra. Muestra comprador desde sesión si existe.
            comprador = session.get("comprador", "Cliente")
            return render_template("compra_realizada.html", comprador=comprador)

        @self.app.route("/ventas")
        def ventas():
            # Consulta que devuelve ventas con datos del comprador (join)
            query = """
                SELECT v.Id_Venta AS id,
                    c.Nombre AS comprador,
                    v.Fecha_Venta AS fecha,
                    v.Total AS total,
                    v.Usuario_D_Creacion AS usuario_creacion,
                    v.Fecha_Hora_Creacion AS fecha_creacion
                FROM venta v
                INNER JOIN comprador c ON v.Id_Comprador = c.Id_Comprador
                ORDER BY v.Id_Venta DESC
            """

            self.cursor.execute(query)
            ventas = self.cursor.fetchall()  # lista de ventas como diccionarios

            return render_template("ventas.html", ventas=ventas)
        
        @self.app.route("/ventas/detalle/<int:id_venta>")
        def venta_detalle(id_venta):
            # Consulta que devuelve el detalle de una venta dada (productos, cantidad, precio, subtotal)
            query = """
                SELECT 
                    p.Nombre_Producto AS producto,
                    d.Cantidad AS cantidad,
                    d.Precio_Unitario AS precio,
                    d.Subtotal AS subtotal
                FROM venta_detalle d
                INNER JOIN producto p ON d.Id_Producto = p.Id_Producto
                WHERE d.Id_Venta = %s
            """

            self.cursor.execute(query, (id_venta,))
            detalle = self.cursor.fetchall()

            return render_template("detalle_venta.html", detalle=detalle, id_venta=id_venta)


    def ejecutar(self):
        # Método que ejecuta el servidor Flask en modo debug (útil para desarrollo).
        # ⚠️ En producción, NO uses debug=True; utiliza un servidor WSGI (gunicorn/uwsgi) y configura logging.
        self.app.run(debug=True)

if __name__ == '__main__':
    # Punto de entrada del script: crea la app y la ejecuta.
    web = PaginaWeb(__name__)
    web.ejecutar()

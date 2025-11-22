from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import mysql.connector

class PaginaWeb:
    def __init__(self, nombre):
        self.app = Flask(nombre)
        self.app.secret_key = "superclave"

        # 🔹 CONEXIÓN A MYSQL (AGREGADO)
        self.db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",  # si tu MySQL tiene contraseña, agrégala aquí
            database="postres"
        )
        self.cursor = self.db.cursor(dictionary=True)

        self.configurar_rutas()

    def configurar_rutas(self):

        # --------------------------
        # 🔹 LOGIN POST (AGREGADO)
        # --------------------------
        @self.app.route("/login", methods=["POST"])
        def login_post():
            usuario = request.form.get("usuario")

            try:
                usuario = int(usuario)  # convierte la cadena a número
            except:
                 return render_template("login.html", error="Usuario inválido")

            password = request.form.get("password")

            query = """
                SELECT * FROM usuario 
                WHERE Id_Usuario=%s AND Contraseña=%s 
            """
            self.cursor.execute(query, (usuario, password))
            datos = self.cursor.fetchone()

            if datos:
                session["usuario"] = datos["Nombre"]
                return redirect(url_for("bienvenido"))
            else:
                return render_template("login.html", error="Usuario o contraseña incorrectos")

        # --------------------------
        # 🔹 Página de Bienvenida
        # --------------------------
        @self.app.route("/bienvenido")
        def bienvenido():
            nombre = session.get("usuario", "Usuario")
            return render_template("bienvenido.html", nombre=nombre)

        # --------------------------
        # 🔹 AQUI EMPIEZA TU CÓDIGO ORIGINAL
        # --------------------------

        @self.app.route("/agregar_carrito", methods=["POST"])
        def agregar_carrito():
            producto = {
                "titulo": request.form.get("titulo"),
                "precio": float(request.form.get("precio") or 0),
                "imagen": request.form.get("imagen"),
                "cantidad": 1
            }

            if "carrito" not in session:
                session["carrito"] = []

            existe = False
            for item in session["carrito"]:
                if item["titulo"] == producto["titulo"]:
                    item["cantidad"] += 1
                    existe = True
                    break

            if not existe:
                session["carrito"].append(producto)

            session.modified = True
            return "OK"

        @self.app.route("/carrito")
        def carrito():
            carrito = session.get("carrito", [])
            return render_template("carrito.html", carrito=carrito)

        @self.app.route("/eliminar_item/<titulo>")
        def eliminar_item(titulo):
            carrito = session.get("carrito", [])
            carrito = [item for item in carrito if item["titulo"] != titulo]
            session["carrito"] = carrito
            session.modified = True
            return redirect(url_for("carrito"))

        @self.app.route("/actualizar_cantidad", methods=["POST"])
        def actualizar_cantidad():
            titulo = request.form.get("titulo")
            accion = request.form.get("accion")

            carrito = session.get("carrito", [])

            removed = False
            nueva_cantidad = None

            for item in carrito:
                if item["titulo"] == titulo:
                    if accion == "sumar":
                        item["cantidad"] = int(item.get("cantidad", 0)) + 1
                    elif accion == "restar":
                        item["cantidad"] = int(item.get("cantidad", 0)) - 1

                    if item["cantidad"] <= 0:
                        carrito = [i for i in carrito if i["titulo"] != titulo]
                        removed = True
                        nueva_cantidad = 0
                    else:
                        nueva_cantidad = item["cantidad"]
                    break

            session["carrito"] = carrito
            session.modified = True

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return jsonify({"ok": True, "cantidad": nueva_cantidad or 0, "removed": removed})

            return redirect(url_for("carrito"))

        @self.app.route("/")
        def index():
            return render_template("index.html")

        @self.app.route('/nosotros')
        def nosotros():
            return render_template('nosotros.html')

        @self.app.route("/contacto", methods=["GET", "POST"])
        def contacto():
            mensaje_enviado = False
            if request.method == "POST":
                nombre = request.form.get("nombre")
                correo = request.form.get("correo")
                telefono = request.form.get("telefono")
                mensaje = request.form.get("mensaje")
                mensaje_enviado = True
            return render_template("contacto.html", mensaje_enviado=mensaje_enviado)

        @self.app.route('/login')
        def login():
            return render_template('login.html')

        @self.app.route('/producto')
        def producto():
            query = "SELECT * FROM producto"
            self.cursor.execute(query)
            productos = self.cursor.fetchall()
            return render_template("producto.html", productos=productos)

        @self.app.route('/producto_detalle')
        def producto_detalle():
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
            session["carrito"] = []
            session.modified = True
            return jsonify({"ok": True})
        
        @self.app.route("/gestion_productos")
        def gestion_productos():
            query = "SELECT * FROM producto"
            self.cursor.execute(query)
            productos = self.cursor.fetchall()
            return render_template("gestion_productos.html", productos=productos)

        @self.app.route("/producto/agregar", methods=["GET","POST"])
        def agregar_producto():
            if request.method == "GET":
                 return render_template("agregar_producto.html")
            
            nombre = request.form["nombre"]
            descripcion = request.form["descripcion"]
            imagen = request.form["imagen"]
            precio = request.form["precio"]
            stock = request.form["stock"]
            fecha = request.form["fecha"]

            query = """
                INSERT INTO producto 
                (Nombre_Producto, Descripcion, Imagen, Precio, Stock, Fecha_Vencimiento, Usuario_D_Creacion, Fecha_Hora_Creacion)
                VALUES (%s, %s, %s, %s, %s, %s, 'admin', NOW())
            """

            valores = (nombre, descripcion, imagen, precio, stock, fecha)

            self.cursor.execute(query, valores)
            self.db.commit()

            return redirect("/gestion_productos")
        
        @self.app.route("/producto/editar/<int:id>", methods=["GET", "POST"])
        def editar_producto(id):

            if request.method == "GET":
                self.cursor.execute("SELECT * FROM producto WHERE Id_Producto=%s", (id,))
                producto = self.cursor.fetchone()
                return render_template("editar_producto.html", producto=producto)

            # Si es POST → guardar cambios
            nombre = request.form["nombre"]
            descripcion = request.form["descripcion"]
            imagen = request.form["imagen"]
            precio = request.form["precio"]
            stock = request.form["stock"]
            fecha = request.form["fecha"]

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
            query = "DELETE FROM producto WHERE Id_Producto=%s"
            self.cursor.execute(query, (id,))
            self.db.commit()
            return redirect("/gestion_productos")


    def ejecutar(self):
        self.app.run(debug=True)

if __name__ == '__main__':
    web = PaginaWeb(__name__)
    web.ejecutar()

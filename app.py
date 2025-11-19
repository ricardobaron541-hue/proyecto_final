from flask import Flask, render_template, request, session, redirect, url_for, jsonify

class PaginaWeb:
    def __init__(self, nombre):
        self.app = Flask(nombre)
        self.app.secret_key = "superclave"
        self.configurar_rutas()

    def configurar_rutas(self):

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

                    # eliminar si 0 o menos
                    if item["cantidad"] <= 0:
                        carrito = [i for i in carrito if i["titulo"] != titulo]
                        removed = True
                        nueva_cantidad = 0
                    else:
                        nueva_cantidad = item["cantidad"]
                    break

            session["carrito"] = carrito
            session.modified = True

            # si la petición viene por fetch/ajax devolvemos json para actualizar en el DOM
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return jsonify({"ok": True, "cantidad": nueva_cantidad or 0, "removed": removed})

            # compatibilidad: redirigir si no es ajax
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
            return render_template('producto.html')

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


    def ejecutar(self):
        self.app.run(debug=True)


if __name__ == '__main__':
    web = PaginaWeb(__name__)
    web.ejecutar()


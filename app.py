from flask import Flask, render_template, request

class PaginaWeb:
    def __init__(self, nombre):
        self.app = Flask(nombre)
        self.configurar_rutas()

    def configurar_rutas(self):
        @self.app.route('/')
        def inicio():
            return render_template('index.html')

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

                # Aquí luego podrás guardar esos datos en tu base de datos si quieres
                mensaje_enviado = True  # activa el cuadro de confirmación

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



    def ejecutar(self):
        self.app.run(debug=True)


if __name__ == '__main__':
    web = PaginaWeb(__name__)
    web.ejecutar()

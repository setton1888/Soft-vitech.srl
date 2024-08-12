import os
import tkinter as tk
from tkinter import messagebox, ttk
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import psycopg2
from datetime import datetime
from ttkthemes import ThemedTk  # Importar para aplicar temas


# Clase Producto
class Producto:
    def __init__(self, nombre, descripcion, precio, cantidad):
        self.nombre = nombre
        self.descripcion = descripcion
        self.precio = precio
        self.cantidad = cantidad

    def save(self, conn):
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO productos (nombre, descripcion, precio, cantidad)
                VALUES (%s, %s, %s, %s)
                RETURNING id;
            """, (self.nombre, self.descripcion, self.precio, self.cantidad))
            conn.commit()
            print("Producto guardado correctamente.")
            messagebox.showinfo("Éxito", f"Producto '{self.nombre}' guardado correctamente.")


# Clase Venta
class Venta:
    def __init__(self, fecha, cliente, productos):
        self.fecha = fecha
        self.cliente = cliente
        self.productos = productos

    def save(self, conn):
        with conn.cursor() as cursor:
            try:
                cursor.execute("""
                    INSERT INTO ventas (fecha, cliente)
                    VALUES (%s, %s) RETURNING id;
                """, (self.fecha, self.cliente))
                venta_id = cursor.fetchone()[0]

                for producto in self.productos:
                    cursor.execute("""
                        INSERT INTO ventas_productos (venta_id, producto_id, cantidad)
                        VALUES (%s, %s, %s);
                    """, (venta_id, producto['id'], producto['cantidad']))

                conn.commit()
                return venta_id
            except psycopg2.Error as e:
                print(f"Error al guardar la venta: {e}")
                conn.rollback()
                return None


# Conexión a la base de datos
def connect_db():
    try:
        conn = psycopg2.connect(
            dbname='Inventario',  # Nombre de tu base de datos
            user='postgres',  # Nombre del usuario
            password='Batman22',  # Contraseña del usuario
            host='localhost',  # Host
            port='5432'  # Puerto de PostgreSQL
        )
        print("Conexión exitosa a la base de datos.")
        return conn
    except psycopg2.Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None


# Generar factura en PDF
def generar_factura(venta, productos):
    file_name = f"factura_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    c = canvas.Canvas(file_name, pagesize=letter)
    width, height = letter

    # Agregar logo
    logo_path = "logo.png"  # Asegúrate de que el logo está en esta ruta
    if os.path.exists(logo_path):
        logo = ImageReader(logo_path)
        c.drawImage(logo, 40, height - 100, width=100, height=80)
    else:
        print("El archivo del logo no se encontró en la ruta especificada.")

    # Información de la empresa
    c.drawString(200, height - 50, "Vitech.SRL")
    c.drawString(200, height - 70, "Teléfono: +1 (849) 207-479")

    # Información de la factura
    c.drawString(100, height - 140, f"Factura {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.drawString(100, height - 160, f"Cliente: {venta['cliente']}")
    c.drawString(100, height - 180, f"Fecha: {venta['fecha']}")

    y = height - 220
    subtotal_general = 0  # Sumar todos los subtotales aquí
    for producto in productos:
        subtotal = producto['precio'] * producto['cantidad']
        subtotal_general += subtotal
        c.drawString(100, y,
                     f"Producto: {producto['nombre']}, Precio: {producto['precio']}, Cantidad: {producto['cantidad']}")
        y -= 20

    # Calcular ITBIS y total
    itbis = subtotal_general * 0.18
    total = subtotal_general + itbis

    # Mostrar el subtotal, ITBIS y total en la factura
    c.drawString(100, y - 20, f"Subtotal: {subtotal_general:.2f}")
    c.drawString(100, y - 40, f"ITBIS (18%): {itbis:.2f}")
    c.drawString(100, y - 60, f"Total: {total:.2f}")

    c.save()
    print(f"Factura guardada como {file_name}")

    # Abrir la factura PDF automáticamente
    os.startfile(file_name)


# Realizar una venta
def realizar_venta():
    try:
        fecha = datetime.now()
        cliente = entry_cliente.get().strip()
        producto_id = entry_producto_id.get().strip()
        producto_nombre = entry_producto_nombre.get().strip()
        precio = entry_precio.get().strip()
        cantidad = entry_cantidad.get().strip()

        # Validación de entradas
        if not cliente or not producto_id or not producto_nombre or not precio or not cantidad:
            raise ValueError("Por favor, completa todos los campos.")

        productos = [{
            'id': int(producto_id),
            'nombre': producto_nombre,
            'precio': float(precio),
            'cantidad': int(cantidad)
        }]

        venta = Venta(fecha, cliente, productos)
        conn = connect_db()
        if conn:
            venta_id = venta.save(conn)
            if venta_id:
                generar_factura({'cliente': cliente, 'fecha': fecha}, productos)
                messagebox.showinfo("Éxito", "Venta registrada y factura generada.")
                consultar_facturas()  # Actualizar el historial de facturas después de una venta
            else:
                messagebox.showerror("Error", "Error al registrar la venta.")
            conn.close()
    except ValueError as e:
        messagebox.showerror("Error de entrada", str(e))
    except psycopg2.Error as e:
        print(f"Error en la base de datos: {e}")
        messagebox.showerror("Error", "Error en la conexión a la base de datos.")


# Consultar productos
def consultar_productos():
    conn = connect_db()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM productos")
                productos = cursor.fetchall()

                # Limpiar el treeview antes de mostrar nuevos datos
                for item in tree.get_children():
                    tree.delete(item)

                # Insertar nuevos datos en el treeview
                for producto in productos:
                    tree.insert("", tk.END, values=producto)
        except psycopg2.Error as e:
            print(f"Error al consultar productos: {e}")
            messagebox.showerror("Error", "Error al consultar productos.")
        finally:
            conn.close()


# Consultar facturas
def consultar_facturas():
    conn = connect_db()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT v.id, v.fecha, v.cliente, sum(p.precio * vp.cantidad) as total
                    FROM ventas v
                    JOIN ventas_productos vp ON v.id = vp.venta_id
                    JOIN productos p ON vp.producto_id = p.id
                    GROUP BY v.id, v.fecha, v.cliente
                    ORDER BY v.fecha DESC
                """)
                facturas = cursor.fetchall()

                # Limpiar el treeview antes de mostrar nuevos datos
                for item in tree_facturas.get_children():
                    tree_facturas.delete(item)

                # Insertar nuevos datos en el treeview
                for factura in facturas:
                    tree_facturas.insert("", tk.END, values=factura)
        except psycopg2.Error as e:
            print(f"Error al consultar facturas: {e}")
            messagebox.showerror("Error", "Error al consultar facturas.")
        finally:
            conn.close()


# Crear un nuevo producto
def crear_producto():
    try:
        nombre = entry_nombre.get().strip()
        descripcion = entry_descripcion.get().strip()
        precio = entry_precio_producto.get().strip()
        cantidad = entry_cantidad_producto.get().strip()

        # Validación de entradas
        if not nombre or not descripcion or not precio or not cantidad:
            raise ValueError("Por favor, completa todos los campos.")

        producto = Producto(
            nombre=nombre,
            descripcion=descripcion,
            precio=float(precio),
            cantidad=int(cantidad)
        )

        conn = connect_db()
        if conn:
            producto.save(conn)
            consultar_productos()  # Actualizar la lista de productos
            conn.close()
            # Mostrar mensaje de éxito
            messagebox.showinfo("Éxito", "Producto creado exitosamente.")
    except ValueError as e:
        messagebox.showerror("Error de entrada", str(e))
    except psycopg2.Error as e:
        print(f"Error en la base de datos: {e}")
        messagebox.showerror("Error", "Error en la conexión a la base de datos.")


# Funciones para limpiar las pestañas
def limpiar_ventas():
    entry_cliente.delete(0, tk.END)
    entry_producto_id.delete(0, tk.END)
    entry_producto_nombre.delete(0, tk.END)
    entry_precio.delete(0, tk.END)
    entry_cantidad.delete(0, tk.END)


def limpiar_crear_producto():
    entry_nombre.delete(0, tk.END)
    entry_descripcion.delete(0, tk.END)
    entry_precio_producto.delete(0, tk.END)
    entry_cantidad_producto.delete(0, tk.END)


def limpiar_historial_facturas():
    for item in tree_facturas.get_children():
        tree_facturas.delete(item)


# Configurar la interfaz gráfica
root = ThemedTk(theme="equilux")  # Usar tema oscuro
root.title("Gestión de Inventario")

# Crear un notebook para pestañas
notebook = ttk.Notebook(root)
notebook.grid(row=0, column=0, padx=10, pady=10)

# Frame para la pestaña de ventas
frame_ventas = ttk.Frame(notebook)
notebook.add(frame_ventas, text="Ventas")

label_cliente = tk.Label(frame_ventas, text="Cliente:")
label_cliente.grid(row=0, column=0, padx=10, pady=10)
entry_cliente = tk.Entry(frame_ventas)
entry_cliente.grid(row=0, column=1, padx=10, pady=10)

label_producto_id = tk.Label(frame_ventas, text="ID Producto:")
label_producto_id.grid(row=1, column=0, padx=10, pady=10)
entry_producto_id = tk.Entry(frame_ventas)
entry_producto_id.grid(row=1, column=1, padx=10, pady=10)

label_producto_nombre = tk.Label(frame_ventas, text="Nombre Producto:")
label_producto_nombre.grid(row=2, column=0, padx=10, pady=10)
entry_producto_nombre = tk.Entry(frame_ventas)
entry_producto_nombre.grid(row=2, column=1, padx=10, pady=10)

label_precio = tk.Label(frame_ventas, text="Precio:")
label_precio.grid(row=3, column=0, padx=10, pady=10)
entry_precio = tk.Entry(frame_ventas)
entry_precio.grid(row=3, column=1, padx=10, pady=10)

label_cantidad = tk.Label(frame_ventas, text="Cantidad:")
label_cantidad.grid(row=4, column=0, padx=10, pady=10)
entry_cantidad = tk.Entry(frame_ventas)
entry_cantidad.grid(row=4, column=1, padx=10, pady=10)

button_realizar_venta = tk.Button(frame_ventas, text="Realizar Venta", command=realizar_venta)
button_realizar_venta.grid(row=5, column=0, columnspan=2, pady=10)

button_limpiar_ventas = tk.Button(frame_ventas, text="Limpiar", command=limpiar_ventas)
button_limpiar_ventas.grid(row=6, column=0, columnspan=2, pady=10)

# Tabla de productos
columns = ("ID", "Nombre", "Descripción", "Precio", "Cantidad")
tree = ttk.Treeview(frame_ventas, columns=columns, show='headings')
tree.grid(row=7, column=0, columnspan=2, pady=20)

for col in columns:
    tree.heading(col, text=col)
    tree.column(col, anchor='center')

button_consultar_productos = tk.Button(frame_ventas, text="Consultar Productos", command=consultar_productos)
button_consultar_productos.grid(row=8, column=0, columnspan=2, pady=10)

# Frame para la pestaña de historial de facturas
frame_historial_facturas = ttk.Frame(notebook)
notebook.add(frame_historial_facturas, text="Historial de Facturas")

columns_facturas = ("ID Venta", "Fecha", "Cliente", "Total")
tree_facturas = ttk.Treeview(frame_historial_facturas, columns=columns_facturas, show='headings')
tree_facturas.grid(row=0, column=0, columnspan=2, pady=20)

for col in columns_facturas:
    tree_facturas.heading(col, text=col)
    tree_facturas.column(col, anchor='center')

button_consultar_facturas = tk.Button(frame_historial_facturas, text="Consultar Historial de Facturas",
                                      command=consultar_facturas)
button_consultar_facturas.grid(row=1, column=0, columnspan=2, pady=10)

button_limpiar_historial = tk.Button(frame_historial_facturas, text="Limpiar", command=limpiar_historial_facturas)
button_limpiar_historial.grid(row=2, column=0, columnspan=2, pady=10)

# Frame para la pestaña de creación de productos
frame_crear_producto = ttk.Frame(notebook)
notebook.add(frame_crear_producto, text="Crear Producto")

label_nombre = tk.Label(frame_crear_producto, text="Nombre:")
label_nombre.grid(row=0, column=0, padx=10, pady=10)
entry_nombre = tk.Entry(frame_crear_producto)
entry_nombre.grid(row=0, column=1, padx=10, pady=10)

label_descripcion = tk.Label(frame_crear_producto, text="Descripción:")
label_descripcion.grid(row=1, column=0, padx=10, pady=10)
entry_descripcion = tk.Entry(frame_crear_producto)
entry_descripcion.grid(row=1, column=1, padx=10, pady=10)

label_precio_producto = tk.Label(frame_crear_producto, text="Precio:")
label_precio_producto.grid(row=2, column=0, padx=10, pady=10)
entry_precio_producto = tk.Entry(frame_crear_producto)
entry_precio_producto.grid(row=2, column=1, padx=10, pady=10)

label_cantidad_producto = tk.Label(frame_crear_producto, text="Cantidad:")
label_cantidad_producto.grid(row=3, column=0, padx=10, pady=10)
entry_cantidad_producto = tk.Entry(frame_crear_producto)
entry_cantidad_producto.grid(row=3, column=1, padx=10, pady=10)

button_crear_producto = tk.Button(frame_crear_producto, text="Crear Producto", command=crear_producto)
button_crear_producto.grid(row=4, column=0, columnspan=2, pady=10)

button_limpiar_crear_producto = tk.Button(frame_crear_producto, text="Limpiar", command=limpiar_crear_producto)
button_limpiar_crear_producto.grid(row=5, column=0, columnspan=2, pady=10)

root.mainloop()

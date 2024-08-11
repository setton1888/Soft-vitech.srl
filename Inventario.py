import tkinter as tk
from tkinter import messagebox, ttk
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import psycopg2
from datetime import datetime
import os

# Aplicación Tkinter
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Inventario")
        self.configure(bg="#1E1E1E")

        # Estilo personalizado para el modo oscuro
        style = ttk.Style()
        style.configure('TFrame', background='#1E1E1E')
        style.configure('TLabel', background='#1E1E1E', foreground='#DDDDDD')
        style.configure('TButton', background='#3A3A3A', foreground='#DDDDDD', padding=6)
        style.configure('TEntry', fieldbackground='#2A2A2A', foreground='#DDDDDD')
        style.configure('Treeview', background='#1E1E1E', foreground='#DDDDDD', bordercolor='#3A3A3A')
        style.configure('Treeview.Heading', background='#2A2A2A', foreground='#DDDDDD')

        # Notebook para pestañas
        notebook = ttk.Notebook(self)
        notebook.pack(expand=True, fill='both')

        # Frame para la pestaña de ventas
        frame_ventas = ttk.Frame(notebook)
        notebook.add(frame_ventas, text="Ventas")
        self.create_ventas_frame(frame_ventas)

        # Frame para la pestaña de historial de facturas
        frame_historial_facturas = ttk.Frame(notebook)
        notebook.add(frame_historial_facturas, text="Historial de Facturas")
        self.create_historial_facturas_frame(frame_historial_facturas)

        # Frame para la pestaña de creación de productos
        frame_crear_producto = ttk.Frame(notebook)
        notebook.add(frame_crear_producto, text="Crear Producto")
        self.create_crear_producto_frame(frame_crear_producto)

    def create_ventas_frame(self, frame):
        tk.Label(frame, text="Cliente:", background="#1E1E1E", foreground="#DDDDDD").grid(row=0, column=0, padx=10, pady=10)
        self.entry_cliente = tk.Entry(frame, bg='#2A2A2A', fg='#DDDDDD')
        self.entry_cliente.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(frame, text="ID Producto:", background="#1E1E1E", foreground="#DDDDDD").grid(row=1, column=0, padx=10, pady=10)
        self.entry_producto_id = tk.Entry(frame, bg='#2A2A2A', fg='#DDDDDD')
        self.entry_producto_id.grid(row=1, column=1, padx=10, pady=10)

        tk.Label(frame, text="Nombre Producto:", background="#1E1E1E", foreground="#DDDDDD").grid(row=2, column=0, padx=10, pady=10)
        self.entry_producto_nombre = tk.Entry(frame, bg='#2A2A2A', fg='#DDDDDD')
        self.entry_producto_nombre.grid(row=2, column=1, padx=10, pady=10)

        tk.Label(frame, text="Precio:", background="#1E1E1E", foreground="#DDDDDD").grid(row=3, column=0, padx=10, pady=10)
        self.entry_precio = tk.Entry(frame, bg='#2A2A2A', fg='#DDDDDD')
        self.entry_precio.grid(row=3, column=1, padx=10, pady=10)

        tk.Label(frame, text="Cantidad:", background="#1E1E1E", foreground="#DDDDDD").grid(row=4, column=0, padx=10, pady=10)
        self.entry_cantidad = tk.Entry(frame, bg='#2A2A2A', fg='#DDDDDD')
        self.entry_cantidad.grid(row=4, column=1, padx=10, pady=10)

        tk.Button(frame, text="Realizar Venta", command=self.realizar_venta).grid(row=5, column=0, columnspan=2, pady=10)
        tk.Button(frame, text="Limpiar", command=self.limpiar_ventas).grid(row=6, column=0, columnspan=2, pady=10)

        columns = ("ID", "Nombre", "Descripción", "Precio", "Cantidad")
        self.tree = ttk.Treeview(frame, columns=columns, show='headings')
        self.tree.grid(row=7, column=0, columnspan=2, pady=20)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor='center')

        tk.Button(frame, text="Consultar Productos", command=self.consultar_productos).grid(row=8, column=0, columnspan=2, pady=10)

    def create_historial_facturas_frame(self, frame):
        columns = ("ID Venta", "Fecha", "Cliente", "Total", "Estado")
        self.tree_facturas = ttk.Treeview(frame, columns=columns, show='headings')
        self.tree_facturas.grid(row=0, column=0, columnspan=2, pady=20)

        for col in columns:
            self.tree_facturas.heading(col, text=col)
            self.tree_facturas.column(col, anchor='center')

        tk.Button(frame, text="Consultar Historial de Facturas", command=self.consultar_facturas).grid(row=1, column=0, columnspan=2, pady=10)
        tk.Button(frame, text="Marcar como No Válida", command=self.marcar_no_valida).grid(row=2, column=0, columnspan=2, pady=10)
        tk.Button(frame, text="Eliminar Factura", command=self.eliminar_factura).grid(row=3, column=0, columnspan=2, pady=10)
        tk.Button(frame, text="Limpiar", command=self.limpiar_historial_facturas).grid(row=4, column=0, columnspan=2, pady=10)

    def create_crear_producto_frame(self, frame):
        tk.Label(frame, text="Nombre:", background="#1E1E1E", foreground="#DDDDDD").grid(row=0, column=0, padx=10, pady=10)
        self.entry_nombre = tk.Entry(frame, bg='#2A2A2A', fg='#DDDDDD')
        self.entry_nombre.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(frame, text="Descripción:", background="#1E1E1E", foreground="#DDDDDD").grid(row=1, column=0, padx=10, pady=10)
        self.entry_descripcion = tk.Entry(frame, bg='#2A2A2A', fg='#DDDDDD')
        self.entry_descripcion.grid(row=1, column=1, padx=10, pady=10)

        tk.Label(frame, text="Precio:", background="#1E1E1E", foreground="#DDDDDD").grid(row=2, column=0, padx=10, pady=10)
        self.entry_precio_producto = tk.Entry(frame, bg='#2A2A2A', fg='#DDDDDD')
        self.entry_precio_producto.grid(row=2, column=1, padx=10, pady=10)

        tk.Label(frame, text="Cantidad:", background="#1E1E1E", foreground="#DDDDDD").grid(row=3, column=0, padx=10, pady=10)
        self.entry_cantidad_producto = tk.Entry(frame, bg='#2A2A2A', fg='#DDDDDD')
        self.entry_cantidad_producto.grid(row=3, column=1, padx=10, pady=10)

        tk.Button(frame, text="Crear Producto", command=self.crear_producto).grid(row=4, column=0, columnspan=2, pady=10)
        tk.Button(frame, text="Limpiar", command=self.limpiar_crear_producto).grid(row=5, column=0, columnspan=2, pady=10)

    def conectar_db(self):
        try:
            conn = psycopg2.connect(
                dbname="Inventario",
                user="postgres",
                password="Batman22",
                host="localhost",
                port="5432"
            )
            return conn
        except Exception as e:
            print(f"Error al conectar a la base de datos: {e}")
            messagebox.showerror("Error", "No se pudo conectar a la base de datos")
            return None

    def generar_factura(self, venta, productos):
        file_name = f"factura_{venta['fecha'].replace(' ', '_')}.pdf"
        c = canvas.Canvas(file_name, pagesize=letter)
        width, height = letter

        # Logo de la empresa
        try:
            logo = ImageReader('logo.png')
            c.drawImage(logo, 40, height - 100, width=150, height=75)
        except Exception as e:
            print(f"Error al cargar el logo: {e}")

        # Detalles de la factura
        c.setFont("Helvetica", 12)
        c.drawString(40, height - 150, f"Vitech.SRL")
        c.drawString(40, height - 170, f"Teléfono: +1 (849) 207-479")
        c.drawString(40, height - 190, f"Fecha: {venta['fecha']}")
        c.drawString(40, height - 210, f"Cliente: {venta['cliente']}")
        c.drawString(40, height - 230, "Detalle del Producto:")

        y_position = height - 250
        total = 0

        for producto in productos:
            c.drawString(40, y_position, f"ID: {producto['id']}, Nombre: {producto['nombre']}, Precio: ${producto['precio']:.2f}, Cantidad: {producto['cantidad']}")
            total += producto['precio'] * producto['cantidad']
            y_position -= 20

        c.drawString(40, y_position - 20, f"Total: ${total:.2f}")
        c.save()

        print(f"Factura guardada como {file_name}")
        os.startfile(file_name)

    def realizar_venta(self):
        cliente = self.entry_cliente.get()
        producto_id = int(self.entry_producto_id.get())
        nombre_producto = self.entry_producto_nombre.get()
        precio = float(self.entry_precio.get())
        cantidad = int(self.entry_cantidad.get())

        venta = {'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'cliente': cliente}
        productos = [{'id': producto_id, 'nombre': nombre_producto, 'precio': precio, 'cantidad': cantidad}]

        # Guardar venta en la base de datos y generar factura
        conn = self.conectar_db()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO ventas (fecha, cliente) VALUES (%s, %s) RETURNING id", (venta['fecha'], cliente))
                venta_id = cursor.fetchone()[0]
                for producto in productos:
                    cursor.execute("INSERT INTO detalle_ventas (venta_id, producto_id, nombre, precio, cantidad) VALUES (%s, %s, %s, %s, %s)",
                                   (venta_id, producto['id'], producto['nombre'], producto['precio'], producto['cantidad']))
                conn.commit()
                self.generar_factura(venta, productos)
                messagebox.showinfo("Éxito", "Venta realizada con éxito")
            except Exception as e:
                conn.rollback()
                print(f"Error al guardar la venta: {e}")
                messagebox.showerror("Error", "No se pudo realizar la venta")
            finally:
                cursor.close()
                conn.close()

    def consultar_productos(self):
        conn = self.conectar_db()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT * FROM productos")
                productos = cursor.fetchall()
                for item in self.tree.get_children():
                    self.tree.delete(item)
                for producto in productos:
                    self.tree.insert('', tk.END, values=producto)
            except Exception as e:
                print(f"Error al consultar productos: {e}")
                messagebox.showerror("Error", "No se pudo consultar los productos")
            finally:
                cursor.close()
                conn.close()

    def consultar_facturas(self):
        conn = self.conectar_db()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT id, fecha, cliente, total, estado FROM ventas")
                facturas = cursor.fetchall()
                for item in self.tree_facturas.get_children():
                    self.tree_facturas.delete(item)
                for factura in facturas:
                    self.tree_facturas.insert('', tk.END, values=factura)
            except Exception as e:
                print(f"Error al consultar facturas: {e}")
                messagebox.showerror("Error", "No se pudo consultar el historial de facturas")
            finally:
                cursor.close()
                conn.close()

    def marcar_no_valida(self):
        selected_item = self.tree_facturas.selection()
        if selected_item:
            factura_id = self.tree_facturas.item(selected_item)['values'][0]
            conn = self.conectar_db()
            if conn:
                cursor = conn.cursor()
                try:
                    cursor.execute("UPDATE ventas SET estado = 'No Válida' WHERE id = %s", (factura_id,))
                    conn.commit()
                    messagebox.showinfo("Éxito", "Factura marcada como no válida")
                    self.consultar_facturas()
                except Exception as e:
                    conn.rollback()
                    print(f"Error al marcar la factura como no válida: {e}")
                    messagebox.showerror("Error", "No se pudo marcar la factura como no válida")
                finally:
                    cursor.close()
                    conn.close()

    def eliminar_factura(self):
        selected_item = self.tree_facturas.selection()
        if selected_item:
            factura_id = self.tree_facturas.item(selected_item)['values'][0]
            conn = self.conectar_db()
            if conn:
                cursor = conn.cursor()
                try:
                    cursor.execute("DELETE FROM ventas WHERE id = %s", (factura_id,))
                    conn.commit()
                    messagebox.showinfo("Éxito", "Factura eliminada")
                    self.consultar_facturas()
                except Exception as e:
                    conn.rollback()
                    print(f"Error al eliminar la factura: {e}")
                    messagebox.showerror("Error", "No se pudo eliminar la factura")
                finally:
                    cursor.close()
                    conn.close()

    def limpiar_ventas(self):
        self.entry_cliente.delete(0, tk.END)
        self.entry_producto_id.delete(0, tk.END)
        self.entry_producto_nombre.delete(0, tk.END)
        self.entry_precio.delete(0, tk.END)
        self.entry_cantidad.delete(0, tk.END)

    def limpiar_historial_facturas(self):
        for item in self.tree_facturas.get_children():
            self.tree_facturas.delete(item)

    def limpiar_crear_producto(self):
        self.entry_nombre.delete(0, tk.END)
        self.entry_descripcion.delete(0, tk.END)
        self.entry_precio_producto.delete(0, tk.END)
        self.entry_cantidad_producto.delete(0, tk.END)

    def crear_producto(self):
        nombre = self.entry_nombre.get()
        descripcion = self.entry_descripcion.get()
        precio = float(self.entry_precio_producto.get())
        cantidad = int(self.entry_cantidad_producto.get())

        conn = self.conectar_db()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO productos (nombre, descripcion, precio, cantidad) VALUES (%s, %s, %s, %s)",
                               (nombre, descripcion, precio, cantidad))
                conn.commit()
                messagebox.showinfo("Éxito", "Producto creado exitosamente")
                self.limpiar_crear_producto()
            except Exception as e:
                conn.rollback()
                print(f"Error al crear el producto: {e}")
                messagebox.showerror("Error", "No se pudo crear el producto")
            finally:
                cursor.close()
                conn.close()

# Ejecutar la aplicación
if __name__ == "__main__":
    app = App()
    app.mainloop()

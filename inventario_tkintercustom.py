import customtkinter as ctk
from tkinter import messagebox, filedialog, simpledialog
import tkinter.ttk as ttk
import sqlite3
from datetime import datetime
import cv2
from pyzbar import pyzbar
from PIL import Image, ImageTk
import openpyxl

DB_NAME = 'productos.db'
DELETE_PASSWORD = 'admin123'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            codebar TEXT PRIMARY KEY,
            sku TEXT,
            marca TEXT,
            producto TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS importaciones (
            importacion_no TEXT,
            sku TEXT,
            marca TEXT,
            producto TEXT,
            codebar TEXT,
            lote TEXT,
            fecha_expira TEXT,
            cant_recibida INTEGER,
            cant_rechazada INTEGER,
            cant_aceptada INTEGER,
            observaciones TEXT
        )
    ''')
    conn.commit()
    conn.close()

def buscar_producto_por_codebar(codebar):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT sku, marca, producto, codebar FROM productos WHERE codebar=?', (codebar,))
    result = c.fetchone()
    conn.close()
    return result

def agregar_producto(codebar, sku, marca, producto):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO productos VALUES (?,?,?,?)', (codebar, sku, marca, producto))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Ya existe
    conn.close()

def editar_producto(codebar, sku, marca, producto):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('UPDATE productos SET sku=?, marca=?, producto=? WHERE codebar=?', (sku, marca, producto, codebar))
    conn.commit()
    conn.close()

def agregar_importacion(importacion_no, sku, marca, producto, codebar, lote, fecha_expira, cant_recibida, cant_rechazada, cant_aceptada, observaciones):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO importaciones (
            importacion_no, sku, marca, producto, codebar, lote, fecha_expira,
            cant_recibida, cant_rechazada, cant_aceptada, observaciones
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (importacion_no, sku, marca, producto, codebar, lote, fecha_expira, cant_recibida, cant_rechazada, cant_aceptada, observaciones))
    conn.commit()
    conn.close()

def buscar_importaciones():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT rowid, * FROM importaciones')
    res = c.fetchall()
    conn.close()
    return res

def actualizar_importacion(rowid, importacion_no, sku, marca, producto, codebar, lote, fecha_expira, cant_recibida, cant_rechazada, cant_aceptada, observaciones):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        UPDATE importaciones SET
            importacion_no=?, sku=?, marca=?, producto=?, codebar=?, lote=?, fecha_expira=?,
            cant_recibida=?, cant_rechazada=?, cant_aceptada=?, observaciones=?
        WHERE rowid=?
    ''', (importacion_no, sku, marca, producto, codebar, lote, fecha_expira,
          cant_recibida, cant_rechazada, cant_aceptada, observaciones, rowid))
    conn.commit()
    conn.close()

def eliminar_importacion_por_rowid(rowid):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM importaciones WHERE rowid=?', (rowid,))
    conn.commit()
    conn.close()

def eliminar_todos_los_datos(password):
    if password != DELETE_PASSWORD:
        return False
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM productos')
    c.execute('DELETE FROM importaciones')
    conn.commit()
    conn.close()
    return True

def exportar_importaciones_excel(filas):
    if not filas:
        messagebox.showinfo("Sin datos", "No hay datos para exportar.")
        return
    archivo = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
    if archivo:
        try:
            libro = openpyxl.Workbook()
            hoja = libro.active
            hoja.append(("No. Importación", "SKU", "Marca", "Producto", "CodeBar", "Lote", "Fecha Expira",
                         "Cantidad Recibida", "Cantidad Rechazada", "Cantidad Aceptada", "Observaciones"))
            for fila in filas:
                hoja.append(fila)
            libro.save(archivo)
            messagebox.showinfo("Éxito", "Datos exportados exitosamente.",)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el archivo:\n{e}")

class BarcodeCameraReader(ctk.CTkToplevel):
    def __init__(self, on_detect_callback, camera_index=0):
        super().__init__()
        self.title("Escanear CodeBar")
        self.geometry("500x320")
        self.on_detect = on_detect_callback
        self.running = True
        self.camera_index = camera_index

        self.label = ctk.CTkLabel(self, text="")
        self.label.pack(pady=8)
        self.info = ctk.CTkLabel(self, text="Presiona ESC para cerrar.")
        self.info.pack()
        self.bind("<Destroy>", self.on_destroy)
        self.bind("<Escape>", lambda e: self.cerrar())
        self.after(10, self.video_loop)

    def video_loop(self):
        if not hasattr(self, 'cap'):
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                messagebox.showerror("Error", "No se pudo abrir la cámara.", parent=self)
                self.destroy()
                return
        ret, frame = self.cap.read()
        if ret:
            barcodes = pyzbar.decode(frame)
            for barcode in barcodes:
                barcode_data = barcode.data.decode('utf-8')
                self.on_detect(barcode_data)
                self.running = False
                self.cap.release()
                self.destroy()
                return
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
            img = Image.fromarray(cv2image)
            imgtk = ImageTk.PhotoImage(image=img)
            self.label.configure(image=imgtk)
            self.label.image = imgtk
        if self.running:
            self.after(10, self.video_loop)

    def cerrar(self):
        self.running = False
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
        self.destroy()

    def on_destroy(self, event):
        self.cerrar()

class MainMenu(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Inventario")
        self.geometry("400x360")
        self.hijas_abiertas = []
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        frame = ctk.CTkFrame(self)
        frame.pack(expand=True, fill="both", padx=30, pady=30)
        ctk.CTkLabel(frame, text="Seleccione una opción:", font=("Arial", 15)).pack(pady=20)
        ctk.CTkButton(frame, text="Agregar nuevo producto", command=self.abrir_agregar_producto, width=220).pack(pady=10)
        ctk.CTkButton(frame, text="Agregar nueva importación", command=self.abrir_importacion, width=220).pack(pady=10)
        ctk.CTkButton(frame, text="Eliminar TODOS los datos", command=self.eliminar_todo_dialogo, width=220).pack(pady=10)

    def abrir_agregar_producto(self):
        win = AgregarProducto(self)
        self.hijas_abiertas.append(win)
        win.protocol("WM_DELETE_WINDOW", lambda w=win: self.cerrar_hija(w))
        win.focus_force()

    def abrir_importacion(self):
        win = InventarioApp(self)
        self.hijas_abiertas.append(win)
        win.protocol("WM_DELETE_WINDOW", lambda w=win: self.cerrar_hija(w))
        win.focus_force()

    def cerrar_hija(self, ventana):
        try:
            self.hijas_abiertas.remove(ventana)
        except ValueError:
            pass
        ventana.destroy()

    def on_close(self):
        if self.hijas_abiertas:
            messagebox.showwarning("Atención", "Por favor, cierre primero las otras ventanas.", parent=self)
            return
        if messagebox.askyesno("Salir", "¿Está seguro de querer cerrar el sistema?", parent=self):
            self.destroy()
            
    def eliminar_todo_dialogo(self):
        password = simpledialog.askstring(
            "Eliminar todos los datos",
            "Ingrese clave para eliminar todos los datos:",
            show='*', parent=self)
        if password is None:
            return
        if eliminar_todos_los_datos(password):
            messagebox.showinfo("Éxito", "¡Todos los datos han sido eliminados!", parent=self)
        else:
            messagebox.showerror("Error", "Clave incorrecta. No se eliminaron los datos.",parent=self)

class AgregarProducto(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Agregar Nuevo Producto")
        self.geometry("490x380")
        self.resizable(False, False)

        LABEL_WIDTH = 25
        ENTRY_WIDTH = 32
        BUTTON_WIDTH = 25

        form = ctk.CTkFrame(self)
        form.pack(expand=True, fill="both", padx=30, pady=30)

        ctk.CTkLabel(form, text="Código de barras:", width=LABEL_WIDTH, anchor="w").grid(row=0, column=0, sticky="w", pady=(8,2), padx=8)
        self.entry_codebar = ctk.CTkEntry(form, width=220)
        self.entry_codebar.grid(row=0, column=1, pady=(8,2), padx=8, sticky="w")
        ctk.CTkButton(form, text="Escanear CodeBar", command=self.scan_barcode_camera, width=180)\
            .grid(row=1, column=0, columnspan=2, pady=(0,14), padx=8, sticky="w")

        ctk.CTkLabel(form, text="SKU:", width=LABEL_WIDTH, anchor="w").grid(row=2, column=0, sticky="w", pady=8, padx=8)
        self.entry_sku = ctk.CTkEntry(form, width=220)
        self.entry_sku.grid(row=2, column=1, pady=8, padx=8, sticky="w")
        ctk.CTkLabel(form, text="Marca:", width=LABEL_WIDTH, anchor="w").grid(row=3, column=0, sticky="w", pady=8, padx=8)
        self.entry_marca = ctk.CTkEntry(form, width=220)
        self.entry_marca.grid(row=3, column=1, pady=8, padx=8, sticky="w")
        ctk.CTkLabel(form, text="Producto (Nombre):", width=LABEL_WIDTH, anchor="w").grid(row=4, column=0, sticky="w", pady=8, padx=8)
        self.entry_producto = ctk.CTkEntry(form, width=220)
        self.entry_producto.grid(row=4, column=1, pady=8, padx=8, sticky="w")

        self.btn_guardar = ctk.CTkButton(form, text="Guardar", command=self.guardar_producto, width=180)
        self.btn_guardar.grid(row=5, column=0, pady=18, padx=8, sticky="w")
        ctk.CTkButton(form, text="Buscar por CodeBar", command=self.buscar_producto, width=180)\
            .grid(row=5, column=1, pady=18, padx=8, sticky="w")

        self.btn_editar = ctk.CTkButton(form, text="Editar producto", command=self.editar_producto, width=380, fg_color="#eab308", text_color="black")
        self.btn_editar.grid(row=6, column=0, columnspan=2, pady=(0, 10), padx=8, sticky="w")
        self.btn_editar.configure(state="disabled")

    def scan_barcode_camera(self):
        def on_detect(barcode):
            self.entry_codebar.delete(0, "end")
            self.entry_codebar.insert(0, barcode)
        BarcodeCameraReader(on_detect, camera_index=0)

    def guardar_producto(self):
        codebar = self.entry_codebar.get().strip()
        sku = self.entry_sku.get().strip()
        marca = self.entry_marca.get().strip()
        producto = self.entry_producto.get().strip()
        if not codebar or not sku or not marca or not producto:
            messagebox.showwarning("Campos vacíos", "Todos los campos son obligatorios.", parent=self)
            return
        if buscar_producto_por_codebar(codebar):
            messagebox.showwarning("Duplicado", "El CodeBar ya existe. Use otro o búsquelo.", parent=self)
            self.btn_editar.configure(state="normal")
            return
        agregar_producto(codebar, sku, marca, producto)
        messagebox.showinfo("Éxito", "Producto guardado correctamente.", parent=self)
        self.btn_editar.configure(state="disabled")
        self.destroy()

    def buscar_producto(self):
        codebar = self.entry_codebar.get().strip()
        if not codebar:
            messagebox.showwarning("Ingrese CodeBar", "Debe ingresar un CodeBar para buscar.", parent=self)
            self.btn_editar.configure(state="disabled")
            return
        result = buscar_producto_por_codebar(codebar)
        if result:
            self.entry_sku.delete(0, "end")
            self.entry_sku.insert(0, result[0])
            self.entry_marca.delete(0, "end")
            self.entry_marca.insert(0, result[1])
            self.entry_producto.delete(0, "end")
            self.entry_producto.insert(0, result[2])
            self.btn_editar.configure(state="normal")
            messagebox.showinfo("Encontrado", "Producto encontrado y campos actualizados.", parent=self)
        else:
            self.btn_editar.configure(state="disabled")
            messagebox.showerror("No encontrado", "No existe ese CodeBar.", parent=self)

    def editar_producto(self):
        codebar = self.entry_codebar.get().strip()
        sku = self.entry_sku.get().strip()
        marca = self.entry_marca.get().strip()
        producto = self.entry_producto.get().strip()
        if not codebar or not sku or not marca or not producto:
            messagebox.showwarning("Campos vacíos", "Todos los campos son obligatorios.", parent=self)
            return
        if not buscar_producto_por_codebar(codebar):
            messagebox.showerror("No existe", "No existe un producto con ese CodeBar.", parent=self)
            self.btn_editar.configure(state="disabled")
            return
        editar_producto(codebar, sku, marca, producto)
        messagebox.showinfo("Éxito", "Producto actualizado correctamente.", parent=self)
        self.btn_editar.configure(state="disabled")
        self.destroy()

class InventarioApp(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Agregar Nueva Importación")
        self.geometry("1280x800")
        self.resizable(True, True)

        self.edit_rowid = None  # Guarda rowid en edición

        LABEL_WIDTH = 170
        ENTRY_WIDTH = 200
        BUTTON_WIDTH = 170

        style = ttk.Style()
        style.configure("Treeview", rowheight=28)
        style.map('Treeview', background=[('selected', '#3c82f6')])

        frame1 = ctk.CTkFrame(self)
        frame1.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(frame1, text="CodeBar:", width=LABEL_WIDTH, anchor="w").grid(row=0, column=0, sticky="w", padx=7, pady=7)
        self.entry_codebar = ctk.CTkEntry(frame1, width=ENTRY_WIDTH)
        self.entry_codebar.grid(row=0, column=1, sticky="w", padx=7, pady=7)
        self.entry_codebar.bind("<Return>", self.leer_codebar)
        ctk.CTkButton(frame1, text="Buscar", command=self.leer_codebar, width=BUTTON_WIDTH).grid(row=0, column=2, padx=7, pady=7, sticky="w")
        ctk.CTkButton(frame1, text="Escanear CodeBar", command=self.scan_barcode_camera, width=BUTTON_WIDTH).grid(row=0, column=3, padx=7, pady=7, sticky="w")

        self.var_sku = ctk.StringVar()
        self.var_marca = ctk.StringVar()
        self.var_producto = ctk.StringVar()
        self.var_codebar = ctk.StringVar()
        ctk.CTkLabel(frame1, text="SKU:", width=LABEL_WIDTH, anchor="w").grid(row=1, column=0, sticky="w", padx=7, pady=7)
        ctk.CTkEntry(frame1, textvariable=self.var_sku, width=ENTRY_WIDTH, state="readonly").grid(row=1, column=1, padx=7, pady=7, sticky="w")
        ctk.CTkLabel(frame1, text="Marca:", width=LABEL_WIDTH, anchor="w").grid(row=1, column=2, sticky="w", padx=7, pady=7)
        ctk.CTkEntry(frame1, textvariable=self.var_marca, width=ENTRY_WIDTH, state="readonly").grid(row=1, column=3, padx=7, pady=7, sticky="w")
        ctk.CTkLabel(frame1, text="Producto:", width=LABEL_WIDTH, anchor="w").grid(row=1, column=4, sticky="w", padx=7, pady=7)
        ctk.CTkEntry(frame1, textvariable=self.var_producto, width=ENTRY_WIDTH, state="readonly").grid(row=1, column=5, padx=7, pady=7, sticky="w")

        frame2 = ctk.CTkFrame(self)
        frame2.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(frame2, text="No. de importación:", width=LABEL_WIDTH, anchor="w").grid(row=0, column=0, padx=7, pady=7, sticky="w")
        self.entry_importacion_no = ctk.CTkEntry(frame2, width=ENTRY_WIDTH)
        self.entry_importacion_no.grid(row=0, column=1, padx=7, pady=7, sticky="w")
        ctk.CTkLabel(frame2, text="Cantidad Recibida:", width=LABEL_WIDTH, anchor="w").grid(row=0, column=2, padx=7, pady=7, sticky="w")
        self.entry_cant_recibida = ctk.CTkEntry(frame2, width=ENTRY_WIDTH)
        self.entry_cant_recibida.grid(row=0, column=3, padx=7, pady=7, sticky="w")
        self.entry_cant_recibida.bind("<KeyRelease>", self.update_cant_aceptada)
        ctk.CTkLabel(frame2, text="Cantidad Rechazada:", width=LABEL_WIDTH, anchor="w").grid(row=0, column=4, padx=7, pady=7, sticky="w")
        self.entry_cant_rechazada = ctk.CTkEntry(frame2, width=ENTRY_WIDTH)
        self.entry_cant_rechazada.grid(row=0, column=5, padx=7, pady=7, sticky="w")
        self.entry_cant_rechazada.bind("<KeyRelease>", self.update_cant_aceptada)
        ctk.CTkLabel(frame2, text="Cantidad Aceptada:", width=LABEL_WIDTH, anchor="w").grid(row=1, column=4, padx=7, pady=7, sticky="w")
        self.var_cant_aceptada = ctk.StringVar()
        ctk.CTkEntry(frame2, textvariable=self.var_cant_aceptada, width=ENTRY_WIDTH, state="readonly").grid(row=1, column=5, padx=7, pady=7, sticky="w")
        ctk.CTkLabel(frame2, text="Lote:", width=LABEL_WIDTH, anchor="w").grid(row=1, column=0, padx=7, pady=7, sticky="w")
        self.entry_lote = ctk.CTkEntry(frame2, width=ENTRY_WIDTH)
        self.entry_lote.grid(row=1, column=1, padx=7, pady=7, sticky="w")
        ctk.CTkLabel(frame2, text="Fecha Expira (dd/mm/aaaa):", width=LABEL_WIDTH, anchor="w").grid(row=1, column=2, padx=7, pady=7, sticky="w")
        self.entry_fecha_expira = ctk.CTkEntry(frame2, width=ENTRY_WIDTH)
        self.entry_fecha_expira.grid(row=1, column=3, padx=7, pady=7, sticky="w")

        frame_obs = ctk.CTkFrame(self)
        frame_obs.pack(fill="x", padx=10, pady=(5, 0))
        ctk.CTkLabel(frame_obs, text="Observaciones:").pack(anchor="w")
        self.entry_observaciones = ctk.CTkTextbox(frame_obs, height=60)
        self.entry_observaciones.pack(fill="x", padx=5, pady=(0, 5))

        frame_agregar = ctk.CTkFrame(self)
        frame_agregar.pack(fill="x", padx=10, pady=(0, 5))
        ctk.CTkButton(frame_agregar, text="Agregar a Tabla", command=self.agregar_a_tabla, width=BUTTON_WIDTH).pack(side="left", padx=5)
        ctk.CTkButton(frame_agregar, text="Exportar a Excel", command=self.exportar_excel, width=BUTTON_WIDTH).pack(side="left", padx=5)
        ctk.CTkButton(frame_agregar, text="Limpiar Tabla", command=self.limpiar_tabla, width=BUTTON_WIDTH).pack(side="left", padx=5)
        self.btn_editar = ctk.CTkButton(frame_agregar, text="Guardar Cambios", command=self.guardar_cambios, width=BUTTON_WIDTH, state="disabled")
        self.btn_editar.pack(side="left", padx=5)
        self.btn_eliminar = ctk.CTkButton(frame_agregar, text="Eliminar Seleccionado", command=self.eliminar_seleccionado, width=BUTTON_WIDTH, fg_color="#dc2626", text_color="white", state="disabled")
        self.btn_eliminar.pack(side="left", padx=5)

        frame3 = ctk.CTkFrame(self)
        frame3.pack(fill="both", expand=True, padx=10, pady=5)
        columnas = (
            "importacion_no", "sku", "marca", "producto", "codebar",
            "lote", "fecha_expira",
            "cant_recibida", "cant_rechazada", "cant_aceptada", "observaciones"
        )
        self.tree = ttk.Treeview(frame3, columns=columnas, show="headings", height=16)
        for col in columnas:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=110 if col not in ("observaciones", "lote", "fecha_expira", "producto") else 150, anchor="center")
        self.tree.pack(fill="both", expand=True, side="left")
        ttk.Scrollbar(frame3, orient="vertical", command=self.tree.yview).pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=lambda f, l: self.tree.yview_moveto(f))

        self.tree.tag_configure("verde", background="#31c48d")
        self.tree.tag_configure("roja", background="#f87171")

        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        self.producto_actual = None
        self.rowid_map = {}

        self.cargar_importaciones()

    def cargar_importaciones(self):
        for x in self.tree.get_children():
            self.tree.delete(x)
        self.rowid_map.clear()
        for row in buscar_importaciones():
            rowid = row[0]
            fila = row[1:]
            tag = "verde" if fila[8] == 0 else "roja"
            item_id = self.tree.insert("", "end", values=fila, tags=(tag,))
            self.rowid_map[item_id] = rowid

    def on_tree_select(self, event):
        selected = self.tree.selection()
        if not selected:
            self.btn_editar.configure(state="disabled")
            self.btn_eliminar.configure(state="disabled")
            self.edit_rowid = None
            return
        item_id = selected[0]
        fila = self.tree.item(item_id)["values"]
        self.entry_importacion_no.delete(0, "end")
        self.entry_importacion_no.insert(0, fila[0])
        self.var_sku.set(fila[1])
        self.var_marca.set(fila[2])
        self.var_producto.set(fila[3])
        self.entry_codebar.delete(0, "end")
        self.entry_codebar.insert(0, fila[4])
        self.entry_lote.delete(0, "end")
        self.entry_lote.insert(0, fila[5])
        self.entry_fecha_expira.delete(0, "end")
        self.entry_fecha_expira.insert(0, fila[6])
        self.entry_cant_recibida.delete(0, "end")
        self.entry_cant_recibida.insert(0, fila[7])
        self.entry_cant_rechazada.delete(0, "end")
        self.entry_cant_rechazada.insert(0, fila[8])
        self.var_cant_aceptada.set(str(fila[9]))
        self.entry_observaciones.delete("0.0", "end")
        self.entry_observaciones.insert("0.0", fila[10])
        self.edit_rowid = self.rowid_map[item_id]
        self.btn_editar.configure(state="normal")
        self.btn_eliminar.configure(state="normal")

    def guardar_cambios(self):
        if self.edit_rowid is None:
            return
        importacion_no = self.entry_importacion_no.get().strip()
        sku = self.var_sku.get().strip()
        marca = self.var_marca.get().strip()
        producto = self.var_producto.get().strip()
        codebar = self.entry_codebar.get().strip()
        lote = self.entry_lote.get().strip()
        fecha_expira = self.entry_fecha_expira.get().strip()
        observaciones = self.entry_observaciones.get("0.0", "end").strip()
        cant_recibida = self.entry_cant_recibida.get().strip()
        cant_rechazada = self.entry_cant_rechazada.get().strip()
        if not (importacion_no and sku and marca and producto and codebar):
            messagebox.showwarning("Campos vacíos", "Todos los campos son obligatorios.",parent=self)
            return
        if not cant_recibida.isdigit() or not cant_rechazada.isdigit():
            messagebox.showwarning("Datos inválidos", "Las cantidades deben ser números enteros.",parent=self)
            return
        try:
            if fecha_expira:
                dt = datetime.strptime(fecha_expira, '%d/%m/%Y')
                fecha_expira_formatted = dt.strftime('%d/%m/%Y')
            else:
                fecha_expira_formatted = ""
        except:
            messagebox.showwarning("Fecha inválida", "La fecha de expiración debe tener formato dd/mm/aaaa.",parent=self)
            return
        recibida = int(cant_recibida)
        rechazada = int(cant_rechazada)
        aceptada = max(0, recibida - rechazada)
        actualizar_importacion(self.edit_rowid, importacion_no, sku, marca, producto, codebar, lote, fecha_expira_formatted, recibida, rechazada, aceptada, observaciones)
        messagebox.showinfo("Éxito", "Importación actualizada correctamente.", parent=self)
        self.cargar_importaciones()
        self.limpiar_campos()

    def eliminar_seleccionado(self):
        if self.edit_rowid is None:
            return
        if messagebox.askyesno("Confirmar", "¿Seguro que deseas eliminar esta importación?" , parent=self):
            eliminar_importacion_por_rowid(self.edit_rowid)
            self.cargar_importaciones()
            self.limpiar_campos()

    def limpiar_campos(self):
        self.entry_importacion_no.delete(0, "end")
        self.entry_cant_recibida.delete(0, "end")
        self.entry_cant_rechazada.delete(0, "end")
        self.var_cant_aceptada.set("")
        self.entry_lote.delete(0, "end")
        self.entry_fecha_expira.delete(0, "end")
        self.entry_observaciones.delete("0.0", "end")
        self.entry_codebar.delete(0, "end")
        self.var_sku.set("")
        self.var_marca.set("")
        self.var_producto.set("")
        self.btn_editar.configure(state="disabled")
        self.btn_eliminar.configure(state="disabled")
        self.edit_rowid = None

    def leer_codebar(self, event=None):
        codebar = self.entry_codebar.get().strip()
        producto = buscar_producto_por_codebar(codebar)
        if producto:
            self.var_sku.set(producto[0])
            self.var_marca.set(producto[1])
            self.var_producto.set(producto[2])
            self.var_codebar.set(producto[3])
            self.producto_actual = producto
            self.entry_importacion_no.focus_set()
        else:
            self.var_sku.set("")
            self.var_marca.set("")
            self.var_producto.set("")
            self.var_codebar.set("")
            self.producto_actual = None
            messagebox.showerror("No encontrado", "Producto no existe en la base de datos.", parent=self)

    def scan_barcode_camera(self):
        def on_detect(barcode):
            self.entry_codebar.delete(0, "end")
            self.entry_codebar.insert(0, barcode)
            self.leer_codebar()
        BarcodeCameraReader(on_detect, camera_index=0)

    def update_cant_aceptada(self, event=None):
        try:
            recibida = int(self.entry_cant_recibida.get())
        except:
            recibida = 0
        try:
            rechazada = int(self.entry_cant_rechazada.get())
        except:
            rechazada = 0
        aceptada = max(0, recibida - rechazada)
        self.var_cant_aceptada.set(str(aceptada))

    def agregar_a_tabla(self):
        if not self.producto_actual:
            messagebox.showwarning("Sin producto", "Debe buscar primero un producto válido.", parent=self)
            return
        importacion_no = self.entry_importacion_no.get().strip()
        cant_recibida = self.entry_cant_recibida.get().strip()
        cant_rechazada = self.entry_cant_rechazada.get().strip()
        lote = self.entry_lote.get().strip()
        fecha_expira = self.entry_fecha_expira.get().strip()
        observaciones = self.entry_observaciones.get("0.0", "end").strip()
        if not importacion_no:
            messagebox.showwarning("Campo requerido", "Debe indicar el número de importación.", parent=self)
            return
        if not cant_recibida.isdigit() or not cant_rechazada.isdigit():
            messagebox.showwarning("Datos inválidos", "Las cantidades deben ser números enteros.", parent=self)
            return
        try:
            if fecha_expira:
                dt = datetime.strptime(fecha_expira, '%d/%m/%Y')
                fecha_expira_formatted = dt.strftime('%d/%m/%Y')
            else:
                fecha_expira_formatted = ""
        except:
            messagebox.showwarning("Fecha inválida", "La fecha de expiración debe tener formato dd/mm/aaaa.", parent=self)
            return

        recibida = int(cant_recibida)
        rechazada = int(cant_rechazada)
        aceptada = max(0, recibida - rechazada)
        fila = (
            importacion_no,
            self.var_sku.get(),
            self.var_marca.get(),
            self.var_producto.get(),
            self.var_codebar.get(),
            lote, fecha_expira_formatted,
            recibida, rechazada, aceptada, observaciones
        )
        agregar_importacion(*fila)
        self.cargar_importaciones()
        self.limpiar_campos()

    def exportar_excel(self):
        filas = [self.tree.item(x)["values"] for x in self.tree.get_children()]
        exportar_importaciones_excel(filas)

    def limpiar_tabla(self):
        for x in self.tree.get_children():
            self.tree.delete(x)
        self.rowid_map.clear()

if __name__ == '__main__':
    init_db()
    app = MainMenu()
    app.mainloop()
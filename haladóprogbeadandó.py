import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
import numpy as np
import cv2

# --- 1. EGYEDI ABLAK A MÉRETEKHEZ (GUI RÉSZ) ---
class MeretMegadasAblak(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Méret beállítása")
        self.geometry("350x230")
        self.resizable(False, False)
        self.configure(bg="#f0f0f0")
        
        tk.Label(self, text="Mekkora legyen a végeredmény (fizikai méret)?", 
                 font=("Arial", 10, "bold"), bg="#f0f0f0").pack(pady=15)

        frame_input = tk.Frame(self, bg="#f0f0f0")
        frame_input.pack(pady=5)

        tk.Label(frame_input, text="Szélesség (cm):", bg="#f0f0f0").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.entry_w = tk.Entry(frame_input, width=10)
        self.entry_w.grid(row=0, column=1, padx=5, pady=5)
        self.entry_w.insert(0, "10")

        tk.Label(frame_input, text="Magasság (cm):", bg="#f0f0f0").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.entry_h = tk.Entry(frame_input, width=10)
        self.entry_h.grid(row=1, column=1, padx=5, pady=5)
        self.entry_h.insert(0, "15")

        tk.Button(self, text="Rendben", bg="#4CAF50", fg="white", width=15, command=self.on_ok).pack(pady=15)
        self.eredmeny = None

    def on_ok(self):
        try:
            w = float(self.entry_w.get().replace(',', '.'))
            h = float(self.entry_h.get().replace(',', '.'))
            self.eredmeny = (w, h)
            self.destroy()
        except ValueError:
            messagebox.showerror("Hiba", "Kérlek számokat adj meg!")

# --- 2. FŐ ALKALMAZÁS ---
class ModernKepSzerkesztoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Képszerkesztő Váz")
        self.root.geometry("1200x800")

        # --- ADATOK ---
        self.eredeti_kep_adat = None   # Itt tároljuk a képet (NumPy array)
        self.megjelenitett_kep = None  # Tkinter kép referencia
        
        self.scale_factor = 1.0        # Kicsinyítési arány
        self.offset_x = 0
        self.offset_y = 0

        self.mode = None               # "vagas", "perspektiva", "meret_cm"
        self.pontok = []               # Kattintások tárolása
        self.cel_cm_meret = None

        self.colors = {"bg_dark": "#2b2b2b", "btn": "#404040", "text": "#ffffff", "accent": "#007acc"}
        self._felepites()

    def _felepites(self):
        main_container = tk.Frame(self.root, bg="gray")
        main_container.pack(fill=tk.BOTH, expand=True)

        # Bal oldali menü
        self.sidebar = tk.Frame(main_container, width=250, bg=self.colors["bg_dark"])
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="ESZKÖZTÁR", bg=self.colors["bg_dark"], fg="#888", font=("Arial", 10, "bold")).pack(pady=(20,10))
        
        # Gombok
        self._gomb("📂 Kép Betöltése", self.cmd_betoltes, kiemelt=True)
        self._gomb("💾 Mentés", self.cmd_mentes)
        tk.Frame(self.sidebar, height=2, bg="#444").pack(fill=tk.X, padx=10, pady=15)
        self._gomb("✂️ Sima Kivágás", lambda: self.mod_valtas("vagas"))
        self._gomb("📐 Perspektíva (Lap)", lambda: self.mod_valtas("perspektiva"))
        self._gomb("📏 Méretre (CM)", self.cmd_meret_bekeres)

        # Vászon
        self.canvas_frame = tk.Frame(main_container, bg="#555")
        self.canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(self.canvas_frame, bg="#555", highlightthickness=0, cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        self.canvas.create_text(400, 300, text="Nincs kép betöltve", fill="#ccc", font=("Arial", 16))

        # Egér események
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

        # Status bar
        self.status_bar = tk.Label(self.root, text="Kész.", bg=self.colors["accent"], fg="white", anchor="w", padx=10)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _gomb(self, text, command, kiemelt=False):
        bg = "#4CAF50" if kiemelt else self.colors["btn"]
        tk.Button(self.sidebar, text=text, command=command, bg=bg, fg=self.colors["text"],
                  bd=0, padx=15, pady=10, anchor="w", cursor="hand2").pack(fill=tk.X, padx=10, pady=5)

    def status(self, msg):
        self.status_bar.config(text=msg)

    def cmd_betoltes(self):
        """
        Betölti a képet Pillow-val (minden formátum + ékezetes fájlnevek támogatása),
        és átalakítja NumPy tömbbé a későbbi szerkesztéshez.
        """
        path = filedialog.askopenfilename(
            filetypes=[("Minden képfájl", "*.*"), ("Képek", "*.jpg;*.png;*.bmp;*.webp;*.tiff")]
        )
        if not path: return

        try:
            # 1. Betöltés Pillow-val (Minden formátumot kezel)
            pil_image = Image.open(path)
            
            # 2. RGB konverzió (hogy ne legyen gond az átlátszósággal vagy grayscale-lel)
            pil_image = pil_image.convert("RGB")
            
            # 3. Tárolás NumPy tömbként (Ez a standard formátum a képmanipulációhoz)
            self.eredeti_kep_adat = np.array(pil_image)
            
            # 4. Megjelenítés
            self._kep_frissitese()
            self.status(f"Sikeres betöltés: {path}")
            self.mod_valtas(None)

        except Exception as e:
            messagebox.showerror("Hiba", f"Nem sikerült megnyitni:\n{e}")

    def _kep_frissitese(self):
        """
        Ez felelős a kép kirajzolásáért. Kiszámolja az arányokat, hogy ráférjen a vászonra.
        """
        if self.eredeti_kep_adat is None: return

        # Vászon méretei
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 10: cw, ch = 800, 600

        img_h, img_w = self.eredeti_kep_adat.shape[:2]

        # Arány számítás
        ratio = min(cw / img_w, ch / img_h)
        self.scale_factor = ratio

        new_w = int(img_w * ratio)
        new_h = int(img_h * ratio)

        # Átméretezzük a MEGJELENÍTÉSHEZ (Pillow resize metódus)
        pil_img = Image.fromarray(self.eredeti_kep_adat)
        resized_pil = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # Offset (középre igazítás)
        self.offset_x = (cw - new_w) // 2
        self.offset_y = (ch - new_h) // 2

        self.megjelenitett_kep = ImageTk.PhotoImage(resized_pil)

        self.canvas.delete("all")
        self.canvas.create_image(self.offset_x, self.offset_y, anchor=tk.NW, image=self.megjelenitett_kep)

    def cmd_mentes(self):
        if self.megjelenitett_kep is None:
            self.status("Nincs mit menteni")
            return
        if isinstance(self.megjelenitett_kep, Image.Image):
            pil_img = self.megjelenitett_kep
        else:
            pil_img = Image.fromarray(self.eredeti_kep_adat)

            filename = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[
                    ("png", "*.png"),
                    ("jpeg", "*.jpeg"),
                    ("bmp", "*.bmp"),
                    ("Mind", "*.*")
                ]
            )
            if filename:
                try:
                    pil_img.save(filename)
                    self.status(f"Mentve: {filename}")
                except Exception as e:
                    self.status(f"Hiba mentéskor: {e}")

    def _vagas_vegrehajtas(self):
        if len(self.pontok) != 2 or self.eredeti_kep_adat is None:
            self.status("Nincs kép vagy nincs 2 pont a vágáshoz")
            return
        
        x1, y1 = self.pontok[0]
        x2, y2 = self.pontok[1]
        x1, x2 = sorted((x1, x2))
        y1, y2 = sorted((y1, y2))

        h, w = self.eredeti_kep_adat.shape[:2]

        #vágás határai képkockán belül
        x1 = max(0, int(x1))
        y1 = max(0, int(y1))
        x2 = min(w, int(x2))
        y2 = min(h, int(y2))

        if x2 <= x1 or y2 <= y1:
            self.status("Érvénytelen vágási téglalap")
            return
        
        #vágás
        self.eredeti_kep_adat = self.eredeti_kep_adat[y1:y2, x1:x2]
        self._kep_frissitese()
        self.status(f"Vágás kész: {x2-x1}x{y2-y1}")

    def _perspektiva_vegrehajtas(self):
        if len(self.pontok) != 4 or self.eredeti_kep_adat is None:
            self.status("Nincs 4 pont vagy nincs kép")
            return

        h, w = self.eredeti_kep_adat.shape[:2]

        pts_src = self.sort_pontok(np.array(self.pontok, dtype=np.float32))

        pts_dst = np.array([[0, 0],          # TL
                            [w, 0],          # TR
                            [w, h],          # BR
                            [0, h]],         # BL
                            dtype=np.float32)

        # warping
        M = cv2.getPerspectiveTransform(pts_src, pts_dst)
        warped = cv2.warpPerspective(self.eredeti_kep_adat, M, (w, h))

        self.eredeti_kep_adat = warped
        self._kep_frissitese()
        self.status("Perspektíva kész")

    def _meret_cm_vegrehajtas(self):
        #dpi=300
        if self.eredeti_kep_adat is None:
            self.status("Nincs megnyitva kép")
            return
        if self.cel_cm_meret is None:
            self.status("Nincs megadva cél-méret (cm)")
            return
        if len(self.pontok) != 2:
            self.status("Nincs kijelölve téglalap")
            return

        # kijelölés koordinátái kép-pixelekben
        x1, y1 = self.pontok[0]
        x2, y2 = self.pontok[1]
        x1, x2 = sorted((x1, x2))
        y1, y2 = sorted((y1, y2))

        h, w = self.eredeti_kep_adat.shape[:2]
        x1 = max(0, int(x1))
        y1 = max(0, int(y1))
        x2 = min(w, int(x2))
        y2 = min(h, int(y2))

        if x2 <= x1 or y2 <= y1:
            self.status("Érvénytelen kijelölés")
            return

        cropped = self.eredeti_kep_adat[y1:y2, x1:x2]   # kivágás

        # pixel átszámítás (300 dpi)
        target_w_cm, target_h_cm = self.cel_cm_meret
        DPI = 300
        CM_TO_INCH = 1 / 2.54
        px_w = int(round(target_w_cm * CM_TO_INCH * DPI))
        px_h = int(round(target_h_cm * CM_TO_INCH * DPI))

        # átméretezés
        pil_crop = Image.fromarray(cropped)
        pil_resized = pil_crop.resize((px_w, px_h), Image.LANCZOS)

        # eredmény visszaírása
        self.eredeti_kep_adat = np.array(pil_resized)
        self._kep_frissitese()
        self.status(f"Méretre igazítva: {target_w_cm}×{target_h_cm} cm  (≈{px_w}×{px_h} px)")

    # ==========================================
    # UI LOGIKA ÉS EGÉRKEZELÉS
    # ==========================================
    def mod_valtas(self, uj_mod):
        self.mode = uj_mod
        self.pontok = []
        self.canvas.delete("overlay")
        msg = {
            "vagas": "KIVÁGÁS: Húzz egy téglalapot!",
            "perspektiva": "PERSPEKTÍVA: Kattints a 4 sarokra!",
            "meret_cm": f"MÉRET: Jelölj ki területet!",
            None: "Kész."
        }
        self.status(msg.get(uj_mod, "Kész."))

    def cmd_meret_bekeres(self):
        ablak = MeretMegadasAblak(self.root)
        self.root.wait_window(ablak)
        if ablak.eredmeny:
            self.cel_cm_meret = ablak.eredmeny
            self.mod_valtas("meret_cm")

    def get_real_coords(self, canvas_x, canvas_y):
        real_x = int((canvas_x - self.offset_x) / self.scale_factor)
        real_y = int((canvas_y - self.offset_y) / self.scale_factor)
        return real_x, real_y

    def on_mouse_down(self, event):
        if self.eredeti_kep_adat is None:
            return
        
        # kattintás koordinátái
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        real_x, real_y = self.get_real_coords(x, y)

        if self.mode == "vagas":
            # csak az utolsó 2 kattintás mentése
            if len(self.pontok) >= 2:
                self.pontok.clear()
                self.canvas.delete("overlay")
            self.pontok.append((real_x, real_y))

        # Vizuális visszajelzés (pötty)
        if self.mode == "perspektiva":
            if len(self.pontok) <4:
                self.pontok.append((real_x, real_y))
                r = 5
                self.canvas.create_oval(x-r, y-r, x+r, y+r, fill="red", tags="overlay")

            if len(self.pontok) == 4:
                self._perspektiva_vegrehajtas()

    def on_mouse_drag(self, event):
        if self.mode is ("vagas" or "meret_cm") and len(self.pontok) > 0:
            # Vizuális keret rajzolása húzás közben
            sx, sy = self.pontok[0]
            sx = int(sx * self.scale_factor) + self.offset_x
            sy = int(sy * self.scale_factor) + self.offset_y
            cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
            self.canvas.delete("rubber")
            self.canvas.create_rectangle(sx, sy, cx, cy, outline="yellow", width=2, tags="rubber")

    def on_mouse_up(self, event):
        if self.mode in ["vagas", "meret_cm"] and len(self.pontok) > 0:
            x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
            real_x, real_y = self.get_real_coords(x, y)
            self.pontok.append((real_x, real_y))
            
            if self.mode == "vagas":
                self._vagas_vegrehajtas()
            elif self.mode == "meret_cm":
                self._meret_cm_vegrehajtas()

    def sort_pontok(self, pts):
        top2, bot2 = pts[np.argsort(pts[:, 1])][:2], pts[np.argsort(pts[:, 1])][2:]
        tl, tr = top2 [np.argsort(top2 [:, 0])]
        bl, br = bot2 [np.argsort(bot2 [:, 0])]
        return np.array([tl, tr, br, bl], dtype=np.float32)

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernKepSzerkesztoApp(root)
    root.mainloop()
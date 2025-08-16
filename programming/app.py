import json, os
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox, simpledialog, filedialog


SWOT_FILE = 'swot_data.json'
PERFORMANCE_FILE = 'performance_data.json'
TASKS_FILE = 'tasks_data.json'
NOTES_FILE = 'notes_data.json'
CATEGORIES = ['Forças', 'Fraquezas', 'Oportunidades', 'Ameaças']

def load_data(file, default):
	if os.path.exists(file):
		with open(file, 'r', encoding='utf-8') as f:
			return json.load(f)
	return default

def save_data(file, data):
	with open(file, 'w', encoding='utf-8') as f:
		json.dump(data, f, ensure_ascii=False, indent=2)

class Toast(ctk.CTkToplevel):
	def __init__(self, master, msg, duration=1500):
		super().__init__(master)
		self.overrideredirect(True)
		self.configure(fg_color="#222")
		label = ctk.CTkLabel(self, text=msg, fg_color="#222", text_color="#fff", font=ctk.CTkFont(size=14, weight="bold"))
		label.pack(ipadx=10, ipady=5)
		self.after(duration, self.destroy)
		self.update_idletasks()
		x = master.winfo_rootx() + master.winfo_width()//2 - self.winfo_width()//2
		y = master.winfo_rooty() + 40
		self.geometry(f'+{x}+{y}')


# --- Sidebar, TopBar, KPIcard (garantir definição antes do uso) ---
class Sidebar(ctk.CTkFrame):
	def __init__(self, master, callback):
		super().__init__(master, width=180, fg_color="#f7f7fa")
		self.pack_propagate(False)
		self.callback = callback
		self.buttons = []
		icons = ["🏠", "📊", "📝", "📅", "📦", "🗒️", "⏱️"]
		tooltips = [
			"Dashboard", "SWOT", "Tarefas", "Desempenho", "Exportar",
			"Anotações", "Temporizador"
		]
		btn_frame = ctk.CTkFrame(self, fg_color="#f7f7fa")
		btn_frame.pack(fill="y", expand=True, pady=12)
		for i, (icon, tip) in enumerate(zip(icons, tooltips)):
			btn = ctk.CTkButton(
				btn_frame,
				text=f"{icon}  {tip}",
				width=160,
				height=38,
				anchor="w",
				fg_color="#f7f7fa",
				text_color="#222",
				hover_color="#e0e0e0",
				font=ctk.CTkFont(size=18, weight="bold" if i==7 else "normal"),
				command=lambda i=i: self.callback(i)
			)
			btn.pack(pady=2, padx=8, anchor="w")
			self.buttons.append(btn)

class TopBar(ctk.CTkFrame):
	def __init__(self, master, search_callback):
		super().__init__(master, height=60, fg_color="#fff")
		self.pack_propagate(False)
		ctk.CTkLabel(self, text="Statistics", font=ctk.CTkFont(size=22, weight="bold"), text_color="#222").pack(side="left", padx=24)
		self.search_var = ctk.StringVar()
		search_entry = ctk.CTkEntry(self, textvariable=self.search_var, width=220, height=36, placeholder_text="Buscar...", fg_color="#f7f7fa", border_color="#e0e0e0", border_width=1)
		search_entry.pack(side="right", padx=24)
		search_entry.bind('<Return>', lambda e: search_callback(self.search_var.get()))

class KPIcard(ctk.CTkFrame):
	def __init__(self, master, title, value, color):
		super().__init__(master, fg_color="#fff", corner_radius=16, border_width=1, border_color="#e0e0e0")
		ctk.CTkLabel(self, text=title, text_color="#888", font=ctk.CTkFont(size=13)).pack(anchor="w", padx=18, pady=(16,0))
		ctk.CTkLabel(self, text=str(value), text_color=color, font=ctk.CTkFont(size=32, weight="bold")).pack(anchor="w", padx=18, pady=(0,16))

class MainPanel(ctk.CTkFrame):
	def __init__(self, master):
		super().__init__(master, fg_color="#f7f7fa")
		self.pages = []
		# 0: Dashboard, 1: SWOT, 2: Tarefas, 3: Desempenho, 4: Exportar, 5: Anotações, 6: Temporizador
		for _ in range(7):
			page = ctk.CTkFrame(self, fg_color="#f7f7fa")
			page.place(relx=0, rely=0, relwidth=1, relheight=1)
			self.pages.append(page)
		self.show_page(0)
	def show_page(self, idx):
		for i, p in enumerate(self.pages):
			p.lift() if i == idx else p.lower()

class SWOTApp(ctk.CTk):
	def __init__(self):
		super().__init__()
		ctk.set_appearance_mode("light")
		ctk.set_default_color_theme("blue")
		self.title("SWOT IDE - Robótica (CTk)")
		self.geometry("1280x800")
		self.resizable(True, True)
		self.sidebar = Sidebar(self, self.switch_page)
		self.sidebar.pack(side="left", fill="y")
		self.topbar = TopBar(self, self.on_search)
		self.topbar.pack(side="top", fill="x")
		self.main_panel = MainPanel(self)
		self.main_panel.pack(side="right", fill="both", expand=True)
		self.create_dashboard()
		self.create_swot_page()
		self.create_tasks_page()
		self.create_perf_page()
		self.create_export_page()
		self.create_notes_page()
		self.create_timer_page()
		self.bind_shortcuts()

	def create_timer_page(self):
		page = self.main_panel.pages[6]
		ctk.CTkLabel(page, text="Temporizador de Competição", font=ctk.CTkFont(size=22, weight="bold"), text_color="#1976d2").pack(pady=(40,10))
		self.timer_time = 120  # segundos
		self.timer_running = False
		self.timer_var = ctk.StringVar(value="02:00")
		self.timer_label = ctk.CTkLabel(page, textvariable=self.timer_var, font=ctk.CTkFont(size=60, weight="bold"), text_color="#222")
		self.timer_label.pack(pady=20)

		btn_frame = ctk.CTkFrame(page, fg_color="#f7f7fa")
		btn_frame.pack(pady=10)
		ctk.CTkButton(btn_frame, text="Iniciar", command=self.start_timer, fg_color="#43a047").pack(side="left", padx=10)
		ctk.CTkButton(btn_frame, text="Pausar", command=self.pause_timer, fg_color="#ffb300").pack(side="left", padx=10)
		ctk.CTkButton(btn_frame, text="Resetar", command=self.reset_timer, fg_color="#e53935").pack(side="left", padx=10)

	def update_timer_display(self):
		m, s = divmod(self.timer_time, 60)
		self.timer_var.set(f"{m:02d}:{s:02d}")

	def timer_tick(self):
		if self.timer_running and self.timer_time > 0:
			self.timer_time -= 1
			self.update_timer_display()
			if self.timer_time == 0:
				self.timer_running = False
				self.toast("Tempo esgotado!")
			else:
				self.after(1000, self.timer_tick)

	def start_timer(self):
		if not self.timer_running and self.timer_time > 0:
			self.timer_running = True
			self.after(1000, self.timer_tick)

	def pause_timer(self):
		self.timer_running = False

	def reset_timer(self):
		self.timer_running = False
		self.timer_time = 120
		self.update_timer_display()

	def switch_page(self, idx):
		self.main_panel.show_page(idx)
		# Atualiza widgets ao trocar de página
		if idx == 1:
			self.load_swot()
		elif idx == 2:
			self.load_tasks()
		elif idx == 3:
			self.load_performance()
	# elif idx == 5:
	#     self.load_notes()

	# --- ANOTAÇÕES RÁPIDAS ---
	def create_notes_page(self):
		page = self.main_panel.pages[5]
		ctk.CTkLabel(page, text="Anotações Rápidas", font=ctk.CTkFont(size=20, weight="bold"), text_color="#222").pack(anchor="w", padx=40, pady=(32,8))
		self.notes_text = ctk.CTkTextbox(page, width=800, height=400, fg_color="#fff", text_color="#222", font=ctk.CTkFont(size=13))
		self.notes_text.pack(padx=40, pady=8)


	def on_search(self, query):
		self.toast(f"Busca: {query}")

	def create_dashboard(self):
		page = self.main_panel.pages[0]
		kpi_frame = ctk.CTkFrame(page, fg_color="#f7f7fa")
		kpi_frame.pack(fill="x", padx=40, pady=(32,8))
		swot = load_data(SWOT_FILE, {c: [] for c in CATEGORIES})
		perf = load_data(PERFORMANCE_FILE, {})
		tasks = load_data(TASKS_FILE, [])
		total_swot = sum(len(swot[c]) for c in CATEGORIES)
		total_perf = len(perf)
		acertos = sum(v['acertos'] for v in perf.values())
		erros = sum(v['erros'] for v in perf.values())
		concluidas = sum(1 for t in tasks if t.get('done'))
		pendentes = len(tasks) - concluidas
		KPIcard(kpi_frame, "Itens SWOT", total_swot, "#1976d2").pack(side="left", padx=18)
		KPIcard(kpi_frame, "Dias de Teste", total_perf, "#1976d2").pack(side="left", padx=18)
		KPIcard(kpi_frame, "Acertos", acertos, "#43a047").pack(side="left", padx=18)
		KPIcard(kpi_frame, "Erros", erros, "#e53935").pack(side="left", padx=18)
		KPIcard(kpi_frame, "Tarefas Concluídas", concluidas, "#00bfae").pack(side="left", padx=18)
		KPIcard(kpi_frame, "Pendentes", pendentes, "#ffb300").pack(side="left", padx=18)

		# Gráfico central (barras)
		chart = ctk.CTkCanvas(page, width=600, height=260, bg="#fff", highlightthickness=0)
		chart.pack(pady=24)
		if perf:
			dates = sorted(perf.keys())[-6:]
			maxv = max([v['acertos']+v['erros'] for v in perf.values()], default=1)
			barw = 48
			gap = 32
			x0 = 60
			y_base = 200
			for i, d in enumerate(dates):
				a = perf[d]['acertos']
				e = perf[d]['erros']
				ha = int((a/maxv)*140)
				he = int((e/maxv)*140)
				chart.create_rectangle(x0+i*(barw+gap), y_base-ha, x0+i*(barw+gap)+barw, y_base, fill='#1976d2', width=0)
				chart.create_rectangle(x0+i*(barw+gap), y_base-he, x0+i*(barw+gap)+barw, y_base, outline='#e53935', width=3)
				chart.create_text(x0+i*(barw+gap)+barw//2, y_base+18, text=d, fill='#888', font=('Segoe UI', 10))
			chart.create_text(40, 40, text='Qtd.', anchor='w', fill='#222', font=('Segoe UI', 12, 'bold'))
			chart.create_text(320, 245, text='Data', anchor='center', fill='#222', font=('Segoe UI', 12, 'bold'))
		else:
			chart.create_text(300, 130, text='Sem dados de desempenho', fill='#888', font=('Segoe UI', 14, 'bold'))

	def create_swot_page(self):
		page = self.main_panel.pages[1]
		ctk.CTkLabel(page, text="Matriz SWOT", font=ctk.CTkFont(size=20, weight="bold"), text_color="#222").pack(anchor="w", padx=40, pady=(32,8))
		swot_frame = ctk.CTkFrame(page, fg_color="#fff")
		swot_frame.pack(padx=40, pady=8, fill="x")
		self.swot_entries = {}
		for i, cat in enumerate(CATEGORIES):
			col = ctk.CTkFrame(swot_frame, fg_color="#f7f7fa", corner_radius=12)
			col.grid(row=0, column=i, padx=12, pady=12, sticky="n")
			ctk.CTkLabel(col, text=cat, font=ctk.CTkFont(size=15, weight="bold"), text_color="#1976d2").pack(pady=(8,4))
			entry = ctk.CTkTextbox(col, width=180, height=220, fg_color="#fff", text_color="#222", font=ctk.CTkFont(size=13))
			entry.pack(padx=4, pady=4)
			self.swot_entries[cat] = entry
		add_frame = ctk.CTkFrame(page, fg_color="#f7f7fa")
		add_frame.pack(padx=40, pady=8, fill="x")
		self.swot_new = ctk.CTkEntry(add_frame, width=320, placeholder_text="Novo item SWOT...")
		self.swot_new.pack(side="left", padx=8)
		self.swot_cat = ctk.CTkComboBox(add_frame, values=CATEGORIES, width=120)
		self.swot_cat.pack(side="left", padx=8)
		self.swot_cat.set(CATEGORIES[0])
		ctk.CTkButton(add_frame, text="Adicionar", command=self.add_swot_item).pack(side="left", padx=8)
		self.load_swot()

	def add_swot_item(self):
		item = self.swot_new.get().strip()
		cat = self.swot_cat.get()
		if not item:
			self.toast("Digite um item para adicionar.")
			return
		data = load_data(SWOT_FILE, {c: [] for c in CATEGORIES})
		data[cat].append(item)
		save_data(SWOT_FILE, data)
		self.swot_new.delete(0, 'end')
		self.load_swot()
		self.toast(f"Adicionado em {cat}!")

	def load_swot(self):
		data = load_data(SWOT_FILE, {c: [] for c in CATEGORIES})
		for cat in CATEGORIES:
			self.swot_entries[cat].delete('1.0', 'end')
			for item in data[cat]:
				self.swot_entries[cat].insert('end', item + '\n')

	def create_tasks_page(self):
		page = self.main_panel.pages[2]
		ctk.CTkLabel(page, text="Tarefas & Agenda", font=ctk.CTkFont(size=20, weight="bold"), text_color="#222").pack(anchor="w", padx=40, pady=(32,8))
		tasks_frame = ctk.CTkFrame(page, fg_color="#fff")
		tasks_frame.pack(padx=40, pady=8, fill="x")
		self.tasks_list = ctk.CTkTextbox(tasks_frame, width=600, height=300, fg_color="#f7f7fa", text_color="#222", font=ctk.CTkFont(size=13))
		self.tasks_list.pack(side="left", padx=8, pady=8)
		add_frame = ctk.CTkFrame(page, fg_color="#f7f7fa")
		add_frame.pack(padx=40, pady=8, fill="x")
		self.task_new = ctk.CTkEntry(add_frame, width=320, placeholder_text="Nova tarefa...")
		self.task_new.pack(side="left", padx=8)
		ctk.CTkButton(add_frame, text="Adicionar", command=self.add_task).pack(side="left", padx=8)
		self.load_tasks()

	def add_task(self):
		task = self.task_new.get().strip()
		if not task:
			self.toast("Digite uma tarefa.")
			return
		data = load_data(TASKS_FILE, [])
		data.append({'desc': task, 'done': False, 'date': datetime.now().strftime('%Y-%m-%d')})
		save_data(TASKS_FILE, data)
		self.task_new.delete(0, 'end')
		self.load_tasks()
		self.toast("Tarefa adicionada!")

	def load_tasks(self):
		data = load_data(TASKS_FILE, [])
		self.tasks_list.delete('1.0', 'end')
		for i, t in enumerate(data):
			status = "✔️" if t.get('done') else "❌"
			self.tasks_list.insert('end', f"{i+1}. {t['desc']} [{status}] ({t['date']})\n")

	def create_perf_page(self):
		page = self.main_panel.pages[3]
		ctk.CTkLabel(page, text="Desempenho", font=ctk.CTkFont(size=20, weight="bold"), text_color="#222").pack(anchor="w", padx=40, pady=(32,8))
		perf_frame = ctk.CTkFrame(page, fg_color="#fff")
		perf_frame.pack(padx=40, pady=8, fill="x")
		self.perf_table = ctk.CTkTextbox(perf_frame, width=600, height=220, fg_color="#f7f7fa", text_color="#222", font=ctk.CTkFont(size=13))
		self.perf_table.pack(padx=8, pady=8)
		add_frame = ctk.CTkFrame(page, fg_color="#f7f7fa")
		add_frame.pack(padx=40, pady=8, fill="x")
		self.date_entry = ctk.CTkEntry(add_frame, width=120, placeholder_text="Data (YYYY-MM-DD)")
		self.date_entry.pack(side="left", padx=8)
		self.acertos_entry = ctk.CTkEntry(add_frame, width=80, placeholder_text="Acertos")
		self.acertos_entry.pack(side="left", padx=8)
		self.erros_entry = ctk.CTkEntry(add_frame, width=80, placeholder_text="Erros")
		self.erros_entry.pack(side="left", padx=8)
		ctk.CTkButton(add_frame, text="Registrar", command=self.add_performance).pack(side="left", padx=8)
		self.load_performance()

	def add_performance(self):
		date = self.date_entry.get().strip()
		if not date:
			date = datetime.now().strftime('%Y-%m-%d')
		try:
			acertos = int(self.acertos_entry.get())
			erros = int(self.erros_entry.get())
		except ValueError:
			self.toast("Digite valores válidos para acertos e erros.")
			return
		data = load_data(PERFORMANCE_FILE, {})
		data[date] = {'acertos': acertos, 'erros': erros}
		save_data(PERFORMANCE_FILE, data)
		self.date_entry.delete(0, 'end')
		self.acertos_entry.delete(0, 'end')
		self.erros_entry.delete(0, 'end')
		self.load_performance()
		self.toast("Desempenho registrado!")

	def load_performance(self):
		data = load_data(PERFORMANCE_FILE, {})
		self.perf_table.delete('1.0', 'end')
		for d in sorted(data.keys()):
			acertos = data[d]['acertos']
			erros = data[d]['erros']
			self.perf_table.insert('end', f"{d} | Acertos: {acertos} | Erros: {erros}\n")

	def create_export_page(self):
		page = self.main_panel.pages[4]
		ctk.CTkLabel(page, text="Exportar Dados", font=ctk.CTkFont(size=20, weight="bold"), text_color="#222").pack(anchor="w", padx=40, pady=(32,8))
		export_frame = ctk.CTkFrame(page, fg_color="#fff")
		export_frame.pack(padx=40, pady=8, fill="x")
		ctk.CTkButton(export_frame, text="Exportar SWOT para CSV", command=self.export_swot_csv).pack(side="left", padx=8, pady=8)
		ctk.CTkButton(export_frame, text="Exportar Desempenho para CSV", command=self.export_perf_csv).pack(side="left", padx=8, pady=8)
		ctk.CTkButton(export_frame, text="Exportar Tarefas para CSV", command=self.export_tasks_csv).pack(side="left", padx=8, pady=8)
		ctk.CTkButton(export_frame, text="Exportar SWOT para JSON", command=self.export_swot_json).pack(side="left", padx=8, pady=8)
		ctk.CTkButton(export_frame, text="Exportar Desempenho para JSON", command=self.export_perf_json).pack(side="left", padx=8, pady=8)
		ctk.CTkButton(export_frame, text="Exportar Tarefas para JSON", command=self.export_tasks_json).pack(side="left", padx=8, pady=8)

	def export_swot_csv(self):
		data = load_data(SWOT_FILE, {c: [] for c in CATEGORIES})
		path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV','*.csv')])
		if not path:
			return
		with open(path, 'w', encoding='utf-8') as f:
			f.write('Categoria,Item\n')
			for cat in CATEGORIES:
				for item in data[cat]:
					f.write(f'{cat},{item}\n')
		self.toast('SWOT exportado para CSV!')

	def export_perf_csv(self):
		data = load_data(PERFORMANCE_FILE, {})
		path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV','*.csv')])
		if not path:
			return
		with open(path, 'w', encoding='utf-8') as f:
			f.write('Data,Acertos,Erros\n')
			for d in sorted(data.keys()):
				f.write(f'{d},{data[d]["acertos"]},{data[d]["erros"]}\n')
		self.toast('Desempenho exportado para CSV!')

	def export_tasks_csv(self):
		data = load_data(TASKS_FILE, [])
		path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV','*.csv')])
		if not path:
			return
		with open(path, 'w', encoding='utf-8') as f:
			f.write('Tarefa,Status,Data\n')
			for t in data:
				status = 'Concluída' if t.get('done') else 'Pendente'
				f.write(f'{t["desc"]},{status},{t["date"]}\n')
		self.toast('Tarefas exportadas para CSV!')

	def export_swot_json(self):
		data = load_data(SWOT_FILE, {c: [] for c in CATEGORIES})
		path = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON','*.json')])
		if not path:
			return
		with open(path, 'w', encoding='utf-8') as f:
			json.dump(data, f, ensure_ascii=False, indent=2)
		self.toast('SWOT exportado para JSON!')

	def export_perf_json(self):
		data = load_data(PERFORMANCE_FILE, {})
		path = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON','*.json')])
		if not path:
			return
		with open(path, 'w', encoding='utf-8') as f:
			json.dump(data, f, ensure_ascii=False, indent=2)
		self.toast('Desempenho exportado para JSON!')

	def export_tasks_json(self):
		data = load_data(TASKS_FILE, [])
		path = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON','*.json')])
		if not path:
			return
		with open(path, 'w', encoding='utf-8') as f:
			json.dump(data, f, ensure_ascii=False, indent=2)
		self.toast('Tarefas exportadas para JSON!')

	def toast(self, msg):
		Toast(self, msg)

	def bind_shortcuts(self):
		self.bind('<Control-f>', lambda e: self.topbar.search_var.set(''))

if __name__ == "__main__":
	app = SWOTApp()
	app.mainloop()

if __name__ == "__main__":
	app = SWOTApp()
	app.mainloop()

	# --- SWOT TAB AVANÇADA ---
	def create_swot_tab(self):
		self.swot_lists = {}
		self.swot_search = ctk.StringVar()
		search_entry = ctk.CTkEntry(self.swot_tab, textvariable=self.swot_search, width=200, placeholder_text="Buscar item SWOT...")
		search_entry.grid(row=0, column=0, padx=8, pady=8, sticky='w')
		search_entry.bind('<KeyRelease>', lambda e: self.load_swot())
		ctk.CTkLabel(self.swot_tab, text="Buscar:").grid(row=0, column=0, sticky='e', padx=(0, 120))
		for i, cat in enumerate(CATEGORIES):
			frame = ctk.CTkFrame(self.swot_tab)
			frame.grid(row=1, column=i, padx=8, pady=8, sticky='n')
			listbox = ctk.CTkTextbox(frame, width=180, height=220, fg_color="#23272e", text_color="#fff", font=ctk.CTkFont(size=13))
			listbox.pack(padx=4, pady=4)
			listbox.bind('<Button-3>', lambda e, c=cat: self.delete_swot_item(c))
			listbox.bind('<Double-Button-1>', lambda e, c=cat: self.edit_swot_item(c))
			self.swot_lists[cat] = listbox
		self.swot_entry = ctk.CTkEntry(self.swot_tab, width=300, placeholder_text="Novo item SWOT...")
		self.swot_entry.grid(row=2, column=0, columnspan=2, padx=8, pady=8, sticky='w')
		self.swot_cat = ctk.CTkComboBox(self.swot_tab, values=CATEGORIES, width=120)
		self.swot_cat.grid(row=2, column=2, padx=8, pady=8, sticky='w')
		self.swot_cat.set(CATEGORIES[0])
		add_btn = ctk.CTkButton(self.swot_tab, text="Adicionar", command=self.add_swot_item)
		add_btn.grid(row=2, column=3, padx=8, pady=8, sticky='w')
		self.load_swot()

	def add_swot_item(self):
		item = self.swot_entry.get().strip()
		cat = self.swot_cat.get()
		if not item:
			self.toast("Digite um item para adicionar.")
			return
		data = load_data(SWOT_FILE, {c: [] for c in CATEGORIES})
		data[cat].append(item)
		save_data(SWOT_FILE, data)
		self.swot_entry.delete(0, 'end')
		self.load_swot()
		self.toast(f"Adicionado em {cat}!")
		self.update_dashboard()

	def load_swot(self):
		data = load_data(SWOT_FILE, {c: [] for c in CATEGORIES})
		search = self.swot_search.get().lower()
		for cat in CATEGORIES:
			self.swot_lists[cat].delete('1.0', 'end')
			for item in data[cat]:
				if search in item.lower():
					self.swot_lists[cat].insert('end', item + '\n')

	def delete_swot_item(self, cat):
		self.toast("Clique duplo para editar. Clique direito para remover (não implementado)")

	def edit_swot_item(self, cat):
		self.toast("Clique duplo para editar (não implementado)")

	# --- TAREFAS/AGENDA ---
	def create_tasks_tab(self):
		self.tasks_list = ctk.CTkTextbox(self.tasks_tab, width=600, height=350, fg_color="#23272e", text_color="#fff", font=ctk.CTkFont(size=13))
		self.tasks_list.pack(pady=10)
		self.task_entry = ctk.CTkEntry(self.tasks_tab, width=400, placeholder_text="Nova tarefa ou evento...")
		self.task_entry.pack(side="left", padx=10)
		add_btn = ctk.CTkButton(self.tasks_tab, text="Adicionar", command=self.add_task)
		add_btn.pack(side="left", padx=4)
		self.load_tasks()

	def add_task(self):
		task = self.task_entry.get().strip()
		if not task:
			self.toast("Digite uma tarefa ou evento.")
			return
		data = load_data(TASKS_FILE, [])
		data.append({'desc': task, 'done': False, 'date': datetime.now().strftime('%Y-%m-%d')})
		save_data(TASKS_FILE, data)
		self.task_entry.delete(0, 'end')
		self.load_tasks()
		self.toast("Tarefa adicionada!")
		self.update_dashboard()

	def load_tasks(self):
		data = load_data(TASKS_FILE, [])
		self.tasks_list.delete('1.0', 'end')
		for i, t in enumerate(data):
			status = "✔️" if t.get('done') else "❌"
			self.tasks_list.insert('end', f"{i+1}. {t['desc']} [{status}] ({t['date']})\n")

	# --- PERFORMANCE TAB ---
	def create_perf_tab(self):
		perf_frame = ctk.CTkFrame(self.perf_tab)
		perf_frame.pack(pady=10)
		ctk.CTkLabel(perf_frame, text="Data (YYYY-MM-DD):").grid(row=0, column=0, padx=4)
		self.date_entry = ctk.CTkEntry(perf_frame, width=100)
		self.date_entry.grid(row=0, column=1, padx=4)
		ctk.CTkLabel(perf_frame, text="Acertos:").grid(row=0, column=2, padx=4)
		self.acertos_entry = ctk.CTkEntry(perf_frame, width=50)
		self.acertos_entry.grid(row=0, column=3, padx=4)
		ctk.CTkLabel(perf_frame, text="Erros:").grid(row=0, column=4, padx=4)
		self.erros_entry = ctk.CTkEntry(perf_frame, width=50)
		self.erros_entry.grid(row=0, column=5, padx=4)
		add_btn = ctk.CTkButton(perf_frame, text="Registrar", command=self.add_performance)
		add_btn.grid(row=0, column=6, padx=8)
		self.perf_table = ctk.CTkTextbox(self.perf_tab, width=600, height=220, fg_color="#23272e", text_color="#fff", font=ctk.CTkFont(size=13))
		self.perf_table.pack(pady=10)
		self.canvas = ctk.CTkCanvas(self.perf_tab, width=600, height=180, bg="#23272e", highlightthickness=0)
		self.canvas.pack(pady=10)
		self.load_performance()

	def add_performance(self):
		date = self.date_entry.get().strip()
		if not date:
			date = datetime.now().strftime('%Y-%m-%d')
		try:
			acertos = int(self.acertos_entry.get())
			erros = int(self.erros_entry.get())
		except ValueError:
			self.toast("Digite valores válidos para acertos e erros.")
			return
		data = load_data(PERFORMANCE_FILE, {})
		data[date] = {'acertos': acertos, 'erros': erros}
		save_data(PERFORMANCE_FILE, data)
		self.date_entry.delete(0, 'end')
		self.acertos_entry.delete(0, 'end')
		self.erros_entry.delete(0, 'end')
		self.load_performance()
		self.toast("Desempenho registrado!")
		self.update_dashboard()

	def load_performance(self):
		data = load_data(PERFORMANCE_FILE, {})
		self.perf_table.delete('1.0', 'end')
		dates = sorted(data.keys())
		acertos_list = []
		erros_list = []
		for d in dates:
			acertos = data[d]['acertos']
			erros = data[d]['erros']
			self.perf_table.insert('end', f"{d} | Acertos: {acertos} | Erros: {erros}\n")
			acertos_list.append(acertos)
			erros_list.append(erros)
		self.draw_graph(dates, acertos_list, erros_list)

	def draw_graph(self, dates, acertos, erros):
		self.canvas.delete('all')
		if not dates:
			return
		max_val = max(acertos + erros) if (acertos + erros) else 1
		bar_width = 20
		gap = 18
		x0 = 40
		y_base = 160
		for i, d in enumerate(dates):
			h = int((acertos[i] / max_val) * 120)
			self.canvas.create_rectangle(x0 + i*(bar_width+gap), y_base-h, x0 + i*(bar_width+gap)+bar_width, y_base, fill='#4caf50')
			h2 = int((erros[i] / max_val) * 120)
			self.canvas.create_rectangle(x0 + i*(bar_width+gap), y_base-h2, x0 + i*(bar_width+gap)+bar_width, y_base, outline='#f44336', width=2)
			self.canvas.create_text(x0 + i*(bar_width+gap)+bar_width//2, y_base+15, text=d, angle=45, anchor='w', font=('Arial', 8), fill='#eee')
		self.canvas.create_text(20, 40, text='Qtd.', anchor='w', fill='#fff')
		self.canvas.create_text(300, 175, text='Data', anchor='center', fill='#fff')

	# --- EXPORT TAB ---
	def create_export_tab(self):
		ctk.CTkLabel(self.export_tab, text="Exportar dados SWOT, Desempenho e Tarefas").pack(pady=20)
		ctk.CTkButton(self.export_tab, text="Exportar SWOT para CSV", command=self.export_swot_csv).pack(pady=8)
		ctk.CTkButton(self.export_tab, text="Exportar Desempenho para CSV", command=self.export_perf_csv).pack(pady=8)
		ctk.CTkButton(self.export_tab, text="Exportar Tarefas para CSV", command=self.export_tasks_csv).pack(pady=8)
		ctk.CTkButton(self.export_tab, text="Exportar SWOT para JSON", command=self.export_swot_json).pack(pady=8)
		ctk.CTkButton(self.export_tab, text="Exportar Desempenho para JSON", command=self.export_perf_json).pack(pady=8)
		ctk.CTkButton(self.export_tab, text="Exportar Tarefas para JSON", command=self.export_tasks_json).pack(pady=8)

	def export_swot_csv(self):
		data = load_data(SWOT_FILE, {c: [] for c in CATEGORIES})
		path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV','*.csv')])
		if not path:
			return
		with open(path, 'w', encoding='utf-8') as f:
			f.write('Categoria,Item\n')
			for cat in CATEGORIES:
				for item in data[cat]:
					f.write(f'{cat},{item}\n')
		self.toast('SWOT exportado para CSV!')

	def export_perf_csv(self):
		data = load_data(PERFORMANCE_FILE, {})
		path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV','*.csv')])
		if not path:
			return
		with open(path, 'w', encoding='utf-8') as f:
			f.write('Data,Acertos,Erros\n')
			for d in sorted(data.keys()):
				f.write(f'{d},{data[d]["acertos"]},{data[d]["erros"]}\n')
		self.toast('Desempenho exportado para CSV!')

	def export_tasks_csv(self):
		data = load_data(TASKS_FILE, [])
		path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV','*.csv')])
		if not path:
			return
		with open(path, 'w', encoding='utf-8') as f:
			f.write('Tarefa,Status,Data\n')
			for t in data:
				status = 'Concluída' if t.get('done') else 'Pendente'
				f.write(f'{t["desc"]},{status},{t["date"]}\n')
		self.toast('Tarefas exportadas para CSV!')

	def export_swot_json(self):
		data = load_data(SWOT_FILE, {c: [] for c in CATEGORIES})
		path = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON','*.json')])
		if not path:
			return
		with open(path, 'w', encoding='utf-8') as f:
			json.dump(data, f, ensure_ascii=False, indent=2)
		self.toast('SWOT exportado para JSON!')

	def export_perf_json(self):
		data = load_data(PERFORMANCE_FILE, {})
		path = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON','*.json')])
		if not path:
			return
		with open(path, 'w', encoding='utf-8') as f:
			json.dump(data, f, ensure_ascii=False, indent=2)
		self.toast('Desempenho exportado para JSON!')

	def export_tasks_json(self):
		data = load_data(TASKS_FILE, [])
		path = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON','*.json')])
		if not path:
			return
		with open(path, 'w', encoding='utf-8') as f:
			json.dump(data, f, ensure_ascii=False, indent=2)
		self.toast('Tarefas exportadas para JSON!')

	# --- TOAST/NOTIFICAÇÃO ---
	def toast(self, msg):
		Toast(self, msg)

	# --- ATALHOS ---
	def bind_shortcuts(self):
		self.bind('<Control-n>', lambda e: self.swot_entry.focus())
		self.bind('<Control-f>', lambda e: self.swot_search.set(''))
		self.bind('<F5>', lambda e: self.update_dashboard())

if __name__ == "__main__":
	app = SWOTApp()
	app.mainloop()
import tkinter as tk
root = tk.Tk()
root.mainloop()

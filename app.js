const API_BASE_URL = "http://localhost:8000"; 
let modoDemoActivo = false;

// 🚗 DICCIONARIO DINÁMICO DE MARCAS Y MODELOS (Para no meter nombres rotos)
// 🚗 DICCIONARIO COMPLETO AUTOMOTRIZ (Mercado Argentino & RuedasMza)
const MODELOS_POR_MARCA = {
    Volkswagen: ["Gol", "Gol Trend", "Bora", "Vento", "Fox", "Suran", "Polo", "Amarok", "Nivus", "T-Cross", "Taos", "Tiguan", "UP", "Voyage", "Saveiro", "Scirocco", "Golf", "CrossFox", "Passat", "Caddy"],
    Chevrolet: ["Onix", "Prisma", "Cruze", "S10", "Tracker", "Corsa", "Classic", "Celta", "Agile", "Spin", "Meriva", "Astra", "Aveo", "Sonic", "Captiva", "Trailblazer", "Zafira"],
    Fiat: ["Cronos", "Palio", "Uno", "Toro", "Siena", "Mobi", "Argo", "Fiorino", "Strada", "Punto", "Idea", "Stilo", "Linea", "500", "Weekend", "Ducato"],
    Renault: ["Sandero", "Logan", "Kangoo", "Duster", "Oroch", "Clio", "Alaskan", "Fluence", "Master", "Megane", "Scenic", "Symbol", "Kwid", "Captur", "Stepway"],
    Ford: ["Fiesta", "Focus", "EcoSport", "Ranger", "Ka", "F-100", "Mondeo", "Kuga", "Transit", "Falcon"],
    Toyota: ["Hilux", "Corolla", "Etios", "Yaris", "SW4", "RAV4", "Prius", "Corona"],
    Peugeot: ["208", "207", "308", "408", "Partner", "2008", "3008", "5008", "206", "307", "407", "Blipper"],
    Citroën: ["C3", "C4", "C4 Lounge", "Berlingo", "C3 Aircross", "C5", "Xsara", "Xsara Picasso", "C4 Picasso"],
    Honda: ["Civic", "HR-V", "CR-V", "Fit", "City", "Accord"],
    Nissan: ["Frontier", "Sentra", "Versa", "March", "Kicks", "Tiida", "X-Trail", "Note"],
    Jeep: ["Renegade", "Compass", "Grand Cherokee", "Wrangler", "Cherokee"],
    Hyundai: ["Tucson", "Santa Fe", "Creta", "i10", "Grand i10", "Elantra", "H-1"],
    Audi: ["A1", "A3", "A4", "A5", "A6", "Q3", "Q5", "Q7", "TT"],
    BMW: ["Serie 1", "Serie 3", "Serie 4", "Serie 5", "X1", "X3", "X5", "X6"],
    Mercedes_Benz: ["Clase A", "Clase B", "Clase C", "Sprinter", "Atego", "AMG"],
    Chery: ["Tiggo", "Tiggo 2", "Tiggo 4", "QQ", "Face", "Fulwin"],
    Suzuki: ["Fun", "Swift", "Grand Vitara", "Jimny"],
    Kia: ["Sportage", "Sorento", "Picanto", "Rio", "Soul", "Carnival"],
    Mitsubishi: ["L200", "Montero", "Outlander", "Lancer"],
    Alfa_Romeo: ["Mito", "Giulietta", "159", "Stelvio"],
    Ram: ["1500", "2500"],
    DS: ["DS 3", "DS 4", "DS 7 Crossback"],
    Subaru: ["Impreza", "Forester", "XV", "Outback"],
    Lifan: ["X60", "Myway", "Foison"],
    Baic: ["X35", "X55", "Senova"],
    BYD: ["F3", "F0"],
    Cadillac: ["Deville", "Seville", "Escalade"],
    Chrysler: ["PT Cruiser", "300C", "Neon", "Caravan"],
    Coradir: ["Tito", "Tita"],
    DFSK: ["C31", "C32", "C35"]
};

// Base de datos volátil para pruebas en Modo Demo
let base_falsa_agencias = [
    { 
        id: "1", 
        nombre: "Automotores Tommy", 
        whatsapp: "5492634912196", 
        zona: "este", 
        intereses: [
            { id: "i1", marca: "VOLKSWAGEN", modelo: "GOL", km_maximo: 150000, combustible: "nafta" }, 
            { id: "i2", marca: "FIAT", modelo: "CRONOS", km_maximo: 0, combustible: "todos" }
        ] 
    },
    { 
        id: "2", 
        nombre: "Mendoza Autos S.A.", 
        whatsapp: "5492615551234", 
        zona: "gm_sur", 
        intereses: [
            { id: "i3", marca: "TOYOTA", modelo: "HILUX", km_maximo: 200000, combustible: "diesel" }
        ] 
    }
];

// 🚀 DISPARADORES INICIALES
document.addEventListener("DOMContentLoaded", () => {
    initEventListeners();
    verificarYcargar();
});

function initEventListeners() {
    document.getElementById("btn-demo").addEventListener("click", activarModoDemo);
    document.getElementById("btn-re-scan").addEventListener("click", verificarYcargar);
    document.getElementById("form-agencia").addEventListener("submit", guardarAgencia);
    document.getElementById("form-interes").addEventListener("submit", guardarInteres);
    document.getElementById("int-marca").addEventListener("change", manejarCambioMarca);
}

// 🔄 MANEJO DE DESPLEGABLES ASOCIADOS (Marca -> Modelo)
function manejarCambioMarca(e) {
    const marcaSeleccionada = e.target.value;
    const selectModelo = document.getElementById("int-modelo");

    if (!marcaSeleccionada) {
        selectModelo.innerHTML = `<option value="">-- ELIGE MARCA PRIMERO --</option>`;
        selectModelo.disabled = true;
        return;
    }

    const modelos = MODELOS_POR_MARCA[marcaSeleccionada] || [];
    selectModelo.innerHTML = `<option value="">-- SELECCIONAR MODELO --</option>` + 
        modelos.map(m => `<option value="${m}">${m}</option>`).join('');
    
    selectModelo.disabled = false;
}

// 🎛️ COMPROBADOR DE ESTADO DEL BACKEND
// 🎛️ COMPROBADOR DE ESTADO DEL BACKEND (Versión mejorada con timeout)
async function verificarYcargar() {
    if (modoDemoActivo) return;
    
    try {
        // Añadimos un pequeño timeout de 3 segundos para dar tiempo al servidor de arrancar
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 3000);

        const res = await fetch(`${API_BASE_URL}/agencias`, { signal: controller.signal });
        clearTimeout(timeoutId);

        if (res.ok) {
            setOnlineState(true);
            cargarAgenciasEnSelects();
            cargarMapeoGeneral();
        } else {
            setOnlineState(false);
        }
    } catch (err) {
        console.warn("Backend no listo todavía, reintentando...");
        setOnlineState(false);
    }
}

function setOnlineState(isOnline) {
    const dot = document.getElementById("status-dot");
    const text = document.getElementById("status-text");
    const badge = document.getElementById("status-badge");
    const contenedor = document.getElementById("contenedor-mapeo");
    const btnDemo = document.getElementById("btn-demo");

    if (isOnline) {
        dot.className = "relative inline-flex rounded-full h-2 w-2 bg-emerald-500";
        text.innerText = "BACKEND CONNECTED (8000)";
        text.className = "text-emerald-400 font-bold";
        badge.className = "bg-slate-900 border border-emerald-950 px-3 py-1.5 rounded-md text-xs flex items-center gap-2 shadow-lg shadow-emerald-950/20";
        btnDemo.style.display = "none";
    } else {
        dot.className = "relative inline-flex rounded-full h-2 w-2 bg-red-500";
        text.innerText = "DISCONNECTED (OFFLINE)";
        text.className = "text-red-500 font-bold";
        badge.className = "bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-md text-xs flex items-center gap-2";
        btnDemo.style.display = "inline-block";
        
        contenedor.innerHTML = `
            <div class="flex flex-col items-center justify-center text-center py-20 border-2 border-dashed border-slate-800 rounded-lg bg-slate-950/40 px-4">
                <div class="text-red-500/20 text-5xl mb-3">
                    <i class="fa-solid fa-triangle-exclamation animate-bounce"></i>
                </div>
                <h3 class="font-black text-red-400 text-sm uppercase tracking-wider">Servidor Local de Python Offline</h3>
                <p class="text-slate-500 text-xs font-sans mt-1 max-w-sm">No se detectó respuesta en <code class="bg-slate-900 text-slate-300 px-1 py-0.5 rounded font-mono text-[11px]">http://localhost:8000</code>.</p>
                <div class="mt-5 p-3 bg-slate-900 border border-slate-800 text-left rounded max-w-md w-full">
                    <p class="text-[10px] text-amber-400 uppercase font-black mb-1">💡 MODO SIMULADOR DISPONIBLE</p>
                    <p class="text-xs text-slate-400 font-sans leading-relaxed">Presioná el botón de arriba <strong>"🧪 FORZAR MODO DEMO"</strong> para inyectar datos falsos y ver el comportamiento de los nuevos filtros avanzados sin prender la terminal.</p>
                </div>
            </div>`;
    }
}

function activarModoDemo() {
    modoDemoActivo = true;
    const dot = document.getElementById("status-dot");
    const text = document.getElementById("status-text");
    const btn = document.getElementById("btn-demo");

    dot.className = "relative inline-flex rounded-full h-2 w-2 bg-amber-500";
    text.innerText = "🧪 EXPERIMENTAL DEMO MODE";
    text.className = "text-amber-400 font-bold";
    btn.innerText = "🔌 SALIR DE DEMO";
    btn.onclick = () => { location.reload(); };
    
    renderizarMapeoData(base_falsa_agencias);
    renderizarSelectData(base_falsa_agencias);
}

// 💾 PROCESO DE POSTS: Registrar Agencia
async function guardarAgencia(e) {
    e.preventDefault();
    
    const data = {
        nombre: document.getElementById("age-nombre").value.trim(),
        whatsapp: document.getElementById("age-whatsapp").value.trim(),
        zona: document.getElementById("age-zona").value
    };

    if (modoDemoActivo) {
        const nueva = { id: Date.now().toString(), ...data, intereses: [] };
        base_falsa_agencias.push(nueva);
        renderizarMapeoData(base_falsa_agencias);
        renderizarSelectData(base_falsa_agencias);
        document.getElementById("form-agencia").reset();
        return;
    }

    try {
        const res = await fetch(`${API_BASE_URL}/agencias`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });

        if (res.ok) {
            // ✅ Si guardó bien, limpia el formulario y actualiza la pantalla
            document.getElementById("form-agencia").reset();
            await verificarYcargar(); 
        } else {
            // 💥 Si el backend responde con 500, 400, etc., leemos qué pasó
            const errData = await res.json().catch(() => ({}));
            const mensajeError = errData.detail || "Error desconocido en el servidor.";
            
            console.error("❌ Error del Backend:", mensajeError);
            alert(`⚠️ No se pudo guardar la agencia:\n${mensajeError}`);
        }

    } catch (err) { 
        console.error("❌ Error de red:", err);
        alert("❌ Error crítico: No hay conexión con el backend (localhost)."); 
    }
}

// 💾 PROCESO DE POSTS: Vincular Filtros Avanzados
// 💾 PROCESO DE POSTS: Vincular Filtros Avanzados
// 💾 PROCESO DE POSTS: Vincular Filtros Avanzados
async function guardarInteres(e) {
    e.preventDefault();
    const agencia_id = document.getElementById("int-agencia").value;
    const marcaRaw = document.getElementById("int-marca").value;
    const modeloRaw = document.getElementById("int-modelo").value;
    const km_maximo = parseInt(document.getElementById("int-km").value);
    const combustible = document.getElementById("int-combustible").value;
    
    // 💵 NUEVOS INPUTS: Captura los valores de precio mínimos y máximos
    const precioMinRaw = document.getElementById("int-precio-min") ? document.getElementById("int-precio-min").value : "";
    const precioMaxRaw = document.getElementById("int-precio-max") ? document.getElementById("int-precio-max").value : "";
    const precio_minimo = precioMinRaw !== "" ? parseInt(precioMinRaw) : null;
    const precio_maximo = precioMaxRaw !== "" ? parseInt(precioMaxRaw) : null;

    if (!agencia_id || !marcaRaw) {
        alert("⚠️ Por favor, seleccioná una Agencia y una Marca antes de enlazar.");
        return;
    }

    const marca = marcaRaw.trim().toUpperCase();
    const modelo = modeloRaw.trim().toUpperCase();

    // El Payload ahora incluye los rangos dinámicos hacia FastAPI
    const bodyPayload = { agencia_id, marca, modelo, km_maximo, combustible, precio_minimo, precio_maximo };

    if (modoDemoActivo) {
        const age = base_falsa_agencias.find(a => a.id === agencia_id);
        if (age) {
            age.intereses.push({ id: Date.now().toString(), marca, modelo, km_maximo, combustible, precio_minimo, precio_maximo });
            renderizarMapeoData(base_falsa_agencias);
            alert("🧪 [DEMO] ¡Filtro con Rango de Precios enlazado con éxito en memoria volátil!");
        }
        resetFormularioInteres();
        return;
    }

    try {
        const res = await fetch(`${API_BASE_URL}/intereses`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(bodyPayload)
        });
        if (res.ok) {
            alert("⚡ ¡Filtro enlazado con éxito! El radar ya está observando este vehículo con los rangos asignados.");
            resetFormularioInteres();
            verificarYcargar();
        } else {
            alert("❌ El servidor rechazó los datos del filtro. Revisá los campos.");
        }
    } catch (err) { 
        console.error(err); 
        alert("❌ Error crítico: No se pudo conectar con el Backend de Python.");
    }
}

function resetFormularioInteres() {
    document.getElementById("int-marca").value = "";
    const selectModelo = document.getElementById("int-modelo");
    selectModelo.innerHTML = `<option value="">-- ELIGE MARCA PRIMERO --</option>`;
    selectModelo.disabled = true;
    document.getElementById("int-km").value = "0";
    document.getElementById("int-combustible").value = "todos";
    // Limpia los nuevos inputs de precio si existen en tu HTML
    if (document.getElementById("int-precio-min")) document.getElementById("int-precio-min").value = "";
    if (document.getElementById("int-precio-max")) document.getElementById("int-precio-max").value = "";
}

async function cargarAgenciasEnSelects() {
    try {
        const res = await fetch(`${API_BASE_URL}/agencias`);
        const data = await res.json();
        renderizarSelectData(data);
    } catch (e) {}
}

async function cargarMapeoGeneral() {
    try {
        // Hacemos las dos peticiones en paralelo
        const [resIntereses, resAgencias] = await Promise.all([
            fetch(`${API_BASE_URL}/mapeo-radar`),
            fetch(`${API_BASE_URL}/agencias`)
        ]);

        const interesesRaw = await resIntereses.json();
        const agenciasRaw = await resAgencias.json();
        
        // Normalizamos los resultados
        const listaIntereses = interesesRaw.data || interesesRaw;
        const listaAgencias = agenciasRaw.data || agenciasRaw;
        
        // Renderizamos con los datos ya cruzados
        renderizarMapeoData(listaIntereses, listaAgencias);
        
    } catch (e) {
        console.error("Error al sincronizar datos:", e);
    }
}

function renderizerZonaTag(zona) {
    const clases = {
        este: "bg-amber-950 border border-amber-800 text-amber-400",
        gm_norte: "bg-purple-950 border border-purple-800 text-purple-400",
        gm_sur: "bg-blue-950 border border-blue-800 text-blue-400",
        valle_uco: "bg-emerald-950 border border-emerald-800 text-emerald-400",
        sur: "bg-teal-950 border border-teal-800 text-teal-400"
    };
    return `<span class="px-2 py-0.5 rounded text-[10px] font-black uppercase ${clases[zona] || 'bg-slate-800'}">${zona}</span>`;
}

function renderizarSelectData(lista) {
    const select = document.getElementById("int-agencia");
    if (lista.length === 0) {
        select.innerHTML = `<option value="">-- NO HAY AGENCIAS CONFIGURADAS --</option>`;
        return;
    }
    select.innerHTML = `<option value="">-- SELECCIONAR AGENCIA --</option>` + 
        lista.map(a => `<option value="${a.id}">${a.nombre.toUpperCase()} [${a.zona.toUpperCase()}]</option>`).join('');
}

// Aceptamos un segundo parámetro: listaAgencias
function renderizarMapeoData(lista, listaAgencias = []) {
    const contenedor = document.getElementById("contenedor-mapeo");
    if (!contenedor) return;

    if (!lista || lista.length === 0) {
        contenedor.innerHTML = `<div class="text-center py-20 text-slate-600 border border-slate-800/40 rounded-lg">Base de datos de agencias vacía o sin intereses.</div>`;
        return;
    }

    // AGRUPACIÓN: Cruzamos los datos usando la listaAgencias
    const agenciasAgrupadas = lista.reduce((acc, item) => {
        if (!acc[item.agencia_id]) {
            // Buscamos la agencia real en la lista que nos pasaron
            const infoAgencia = listaAgencias.find(a => String(a.id) === String(item.agencia_id)) || {};
            
            acc[item.agencia_id] = {
                id: item.agencia_id,
                nombre: infoAgencia.nombre || `Agencia #${item.agencia_id}`,
                whatsapp: infoAgencia.whatsapp || "N/A",
                intereses: []
            };
        }
        acc[item.agencia_id].intereses.push(item);
        return acc;
    }, {});

    const agenciasArray = Object.values(agenciasAgrupadas);

    contenedor.innerHTML = agenciasArray.map(agencia => {
        const interesesAgencia = agencia.intereses || [];

        return `
        <div class="bg-slate-900 border border-slate-800 rounded p-3 hover:border-slate-700 transition-all shadow-sm">
            <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 border-b border-slate-800 pb-2 mb-2">
                <div>
                    <h3 class="font-black text-white text-sm tracking-tight flex items-center gap-1.5 uppercase">
                        <i class="fa-solid fa-folder text-slate-500"></i> ${agencia.nombre || "Agencia Desconocida"}
                    </h3>
                    <div class="flex items-center gap-2 text-[11px] text-slate-400 font-sans mt-0.5">
                        <span class="font-mono text-slate-300"><i class="fa-brands fa-whatsapp text-slate-500"></i> ${agencia.whatsapp || "N/A"}</span>
                    </div>
                </div>
                <button onclick="eliminarAgencia('${agencia.id}')" class="text-[10px] font-bold text-red-400 hover:bg-red-950/40 hover:text-red-300 px-2 py-1 rounded border border-red-900/30 transition-colors cursor-pointer font-mono">
                    [🗑️ BORRAR AGENCIA]
                </button>
            </div>
            
            <div class="mt-2">
                <div class="flex flex-wrap gap-2">
                    ${interesesAgencia.map(i => {
                        const km = parseInt(i.km_maximo) || 0;
                        const txtKM = km > 0 ? ` < ${km/1000}k KM` : '';
                        const txtComb = i.combustible && i.combustible !== 'todos' ? ` (${i.combustible.toUpperCase()})` : '';
                        
                        let txtPrecio = '';
                        const valMin = Number(i.precio_minimo);
                        const valMax = Number(i.precio_maximo);
                        
                        const tieneMin = i.precio_minimo !== null && i.precio_minimo !== undefined && i.precio_minimo !== '';
                        const tieneMax = i.precio_maximo !== null && i.precio_maximo !== undefined && i.precio_maximo !== '';

                        if (tieneMin && tieneMax) {
                            txtPrecio = ` [$${(valMin/1000000).toFixed(1)}M-$${(valMax/1000000).toFixed(1)}M]`;
                        } else if (tieneMax) {
                            txtPrecio = ` [Max: $${(valMax/1000000).toFixed(1)}M]`;
                        } else if (tieneMin) {
                            txtPrecio = ` [Min: $${(valMin/1000000).toFixed(1)}M]`;
                        }
                        
                        return `
                            <span class="inline-flex items-center bg-slate-950 border border-slate-800 text-[11px] font-bold px-2 py-1 rounded gap-2">
                                <span class="text-slate-300">
                                    ${(i.marca || '').toUpperCase()} <span class="text-blue-400 font-black">${(i.modelo || '').toUpperCase()}</span>
                                    <span class="text-slate-500 text-[10px] font-medium">${txtKM}${txtComb}</span>
                                    <span class="text-amber-500 text-[10px] font-black">${txtPrecio}</span>
                                </span>
                                <button onclick="eliminarInteres('${i.id}')" class="text-slate-500 hover:text-red-400 font-extrabold text-xs transition-colors cursor-pointer" title="Remover">×</button>
                            </span>`;
                    }).join('')}
                </div>
            </div>
        </div>`;
    }).join('');
}
// 🗑️ LOGICA REAL DE BORRADOS (Inyectada al final de forma limpia sobre tus firmas originales)
async function eliminarInteres(id) {
    if (!confirm("¿Quitar este vehículo y sus filtros técnicos del radar?")) return;

    if (modoDemoActivo) {
        base_falsa_agencias.forEach(a => {
            a.intereses = a.intereses.filter(i => i.id !== id);
        });
        renderizarMapeoData(base_falsa_agencias);
        return;
    }

    try {
        const res = await fetch(`${API_BASE_URL}/intereses/${id}`, { method: "DELETE" });
        if (res.ok) {
            verificarYcargar();
        } else {
            alert("❌ No se pudo borrar el interés del backend.");
        }
    } catch (err) { 
        console.error("Error en DELETE de interes:", err); 
    }
}

async function eliminarAgencia(id) {
    if (!confirm("¿Eliminar por completo esta agencia y colapsar todos sus radares?")) return;

    if (modoDemoActivo) {
        base_falsa_agencias = base_falsa_agencias.filter(a => a.id !== id);
        renderizarMapeoData(base_falsa_agencias);
        renderizarSelectData(base_falsa_agencias);
        return;
    }

    try {
        const res = await fetch(`${API_BASE_URL}/agencias/${id}`, { method: "DELETE" });
        if (res.ok) {
            verificarYcargar();
        } else {
            alert("❌ No se pudo borrar la agencia del backend.");
        }
    } catch (err) { 
        console.error("Error en DELETE de agencia:", err); 
    }
}

const marcasPorTipo = {
    'autos_utilitarios': ['Volkswagen', 'Fiat', 'Chevrolet', 'Renault', 'Ford', 'Toyota', 'Peugeot', 'Citroën', 'Honda', 'Nissan'],
    'motos': ['Aprilia', 'Bajaj', 'Benelli', 'Beta', 'Brava', 'Corven', 'Ducati', 'Gilera', 'Honda (Motos)', 'Kawasaki', 'Motomel', 'Yamaha (Motos)', 'Zanella'],
    'pesados': ['Iveco', 'Scania', 'Volvo', 'Mercedes Benz (Pesados)', 'Hino']
};

document.getElementById('int-tipo').addEventListener('change', function() {
    const tipo = this.value;
    const selectMarca = document.getElementById('int-marca');
    
    // Limpiar opciones actuales
    selectMarca.innerHTML = '<option value="">-- SELECCIONAR MARCA --</option>';
    
    if (tipo && marcasPorTipo[tipo]) {
        marcasPorTipo[tipo].forEach(marca => {
            const option = document.createElement('option');
            option.value = marca;
            option.textContent = marca;
            selectMarca.appendChild(option);
        });
    }
});
async function activarRadarReal() {
    const btn = document.getElementById('btn-radar');
    const originalText = btn.innerHTML;
    
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> PROCESANDO...';
    btn.disabled = true;

    try {
        const response = await fetch(`${API_BASE_URL}/trigger-match`);
        
        if (!response.ok) throw new Error("Error en el servidor");
        
        const data = await response.json();
        
        alert("✅ ¡Radar ejecutado con éxito! Revisa la terminal para ver los resultados.");
        console.log("🚀 Resultado del Radar:", data);
        
    } catch (error) {
        console.error("❌ Fallo crítico:", error);
        alert("⚠️ Error: No pude conectar con el servidor. ¿Está el uvicorn corriendo en el puerto 8000?");
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}
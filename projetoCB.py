
from flask import Flask, render_template, request, jsonify
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint
import io
import base64
import pandas as pd

app = Flask(__name__)

# Modelo de crescimento bacteriano (logístico)
def bacteria_growth(N, t, r, N_max):
    return r * N * (1 - N / N_max)

# Simulação de corrente e tensão (com ruído)
def generate_voltage_current(materia_organica):
    base_current = np.random.uniform(0.01, 0.05) * materia_organica  # Corrente em A
    base_voltage = np.random.uniform(0.5, 1.5)  # Tensão em V
    noise = np.random.normal(0, 0.005)  # Pequeno ruído
    return base_voltage, base_current + noise

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/simulate', methods=['POST'])
def simulate():
    materia_organica = float(request.form['materia_organica'])
    V, I = generate_voltage_current(materia_organica)
    P = V * I  # Potência gerada (W)

    k = 0.8  # Fator empírico
    r = k * P 

    t = np.linspace(0, 48, 100)  # Tempo em horas
    N0 = 1e6  # Bactérias iniciais
    N_max = 1e9  # Capacidade máxima do sistema
    N = odeint(bacteria_growth, N0, t, args=(r, N_max))

    # Criar tabela completa com todos os dados de crescimento
    tabela_completa = pd.DataFrame({"Tempo (h)": t, "Bactérias": N.flatten().astype(int)})
    tabela_html_completa = tabela_completa.to_html(index=False, classes='table table-striped table-bordered')

    # Criar tabela com dados de crescimento em períodos específicos
    periodos = [6, 12, 24, 48]
    dados_periodos = {"Tempo (h)": [], "Bactérias": []}
    for p in periodos:
        idx = np.abs(t - p).argmin()
        dados_periodos["Tempo (h)"].append(p)
        dados_periodos["Bactérias"].append(int(N[idx]))
    
    tabela_resumida = pd.DataFrame(dados_periodos)
    tabela_html_resumida = tabela_resumida.to_html(index=False, classes='table table-striped table-bordered')

    # Gerar gráfico atualizado
    plt.figure(figsize=(8, 5))
    plt.plot(t, N, label=f'Potência: {P:.5f} W, r: {r:.5f} h⁻¹', color='blue')
    plt.scatter(dados_periodos["Tempo (h)"], dados_periodos["Bactérias"], color='red', zorder=3, label='Períodos Chave')
    plt.xlabel('Tempo (h)')
    plt.ylabel('População de Bactérias')
    plt.title('Crescimento Bacteriano Estimado')
    plt.legend()
    plt.grid()

    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    
    return jsonify({'plot_url': f'data:image/png;base64,{plot_url}', 
                    'tabela_resumida': tabela_html_resumida, 
                    'tabela_completa': tabela_html_completa})

if __name__ == '__main__':
    app.run(debug=True)

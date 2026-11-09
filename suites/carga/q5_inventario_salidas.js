import http from 'k6/http';
import { check, fail } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';
import { randomUUID } from 'k6/crypto';

const api = `${__ENV.API_BASE_URL}/api/v1`;
const productoId = __ENV.QA_PRODUCTO_ID;
const cantidad = Number(__ENV.QA_CANTIDAD_SALIDA || '1');
const motivo = __ENV.QA_MOTIVO_CODIGO || 'CONSUMO_SERVICIO';

const erroresEscenario = new Rate('q5_errores_escenario');
const consultas = new Counter('q5_consultas_inventario');
const salidas = new Counter('q5_salidas_registradas');
const duracionConsulta = new Trend('q5_consulta_inventario_ms');
const duracionSalida = new Trend('q5_registro_salida_ms');

export const options = {
  scenarios: {
    q5_20_usuarios: {
      executor: 'shared-iterations',
      vus: 20,
      iterations: 20,
      maxDuration: '2m',
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<=1500'],
    http_req_failed: ['rate<=0.01'],
    q5_errores_escenario: ['rate<=0.01'],
    q5_consulta_inventario_ms: ['p(95)<=1500'],
    q5_registro_salida_ms: ['p(95)<=1500'],
  },
};

export function setup() {
  if (!__ENV.API_BASE_URL || !__ENV.QA_ADMIN_CORREO || !__ENV.QA_ADMIN_CONTRASENA || !productoId) {
    fail('Define API_BASE_URL, QA_ADMIN_CORREO, QA_ADMIN_CONTRASENA y QA_PRODUCTO_ID.');
  }
  if (!Number.isFinite(cantidad) || cantidad <= 0) {
    fail('QA_CANTIDAD_SALIDA debe ser un número mayor que cero.');
  }

  const login = http.post(
    `${api}/auth/login`,
    JSON.stringify({ correo: __ENV.QA_ADMIN_CORREO, contrasena: __ENV.QA_ADMIN_CONTRASENA }),
    { headers: { 'Content-Type': 'application/json' }, tags: { name: 'POST /auth/login' } },
  );
  if (login.status !== 200 || !login.json('access_token')) {
    fail(`No se pudo iniciar sesión en staging (HTTP ${login.status}).`);
  }
  return { token: login.json('access_token') };
}

export default function (data) {
  const headers = { Authorization: `Bearer ${data.token}` };
  const lectura = http.get(`${api}/productos/${productoId}`, {
    headers,
    tags: { name: 'GET /productos/{id}' },
  });
  const lecturaOk = check(lectura, {
    'consulta de inventario responde 200': (r) => r.status === 200,
  });
  consultas.add(1);
  duracionConsulta.add(lectura.timings.duration);

  if (!lecturaOk) {
    erroresEscenario.add(1);
    return;
  }

  const salida = http.post(
    `${api}/movimientos/salidas`,
    JSON.stringify({
      producto_id: productoId,
      cantidad,
      motivo_codigo: motivo,
      observacion: `Q5 k6 VU ${__VU} iteración ${__ITER}`,
    }),
    {
      headers: {
        ...headers,
        'Content-Type': 'application/json',
        'Idempotency-Key': randomUUID(),
      },
      tags: { name: 'POST /movimientos/salidas' },
    },
  );
  const salidaOk = check(salida, {
    'salida de inventario responde 201': (r) => r.status === 201,
  });
  duracionSalida.add(salida.timings.duration);
  if (salidaOk) {
    salidas.add(1);
  } else {
    erroresEscenario.add(1);
  }
}

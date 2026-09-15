<p align="center">
  <img src="https://github.com/m4c3/hass-hargassner-cloud/raw/main/brands_assets/logo-crop.jpg" alt="Logotipo de Hargassner Cloud" width="400">
</p>

<p align="center"><a href="README.de.md">Deutsch</a> | <a href="README.md">English</a> | <a href="README.fr.md">Français</a> | Español | <a href="README.nb.md">Norsk bokmål</a> | <a href="README.pl.md">Polski</a> | <a href="README.cs.md">Čeština</a></p>

# Hargassner Cloud para Home Assistant

Hargassner Cloud es una integración personalizada de Home Assistant que lee
los datos de calefacción del portal web de Hargassner y los publica como
sensores y sensores binarios.

> [!IMPORTANT]
> Este proyecto independiente no está afiliado ni respaldado por Hargassner.
> Utiliza una API en la nube no documentada que puede cambiar.

## Funciones

- Configuración desde la interfaz con el correo y la contraseña de la cuenta
  Hargassner
- Detección y selección automáticas de instalaciones
- Sin búsqueda manual de ID o secreto de cliente
- Actualización automática de las credenciales públicas del cliente web
- Consultas centralizadas mediante `DataUpdateCoordinator`
- Reautenticación de Home Assistant cuando se rechazan los datos personales
- Intervalo, área sugerida y asignaciones de campos configurables
- Diagnósticos y registros depurados
- Visualización de la versión de software cuando la proporciona la API de nube
- Detección sin límite artificial de acumuladores y circuitos numerados

## Sistemas probados

- **NanoPK:** inicio de sesión, detección de instalaciones y obtención de widgets
  probados con el servicio real
- **Neo-HV 20:** validado con datos de diagnóstico reales y redactados de Home
  Assistant y una prueba de regresión sintética de su topología de widgets

Otros sistemas Hargassner pueden funcionar si ofrecen widgets de nube compatibles,
pero este proyecto todavía no los ha verificado.

## Entidades

Las entidades dependen de los widgets que devuelve la instalación: calefacción,
temperatura exterior, depósito de inercia, acumuladores y circuitos. Se detectan
todos los widgets `BOILER` numerados y todos los tipos numerados
`HEATING_CIRCUIT_*`, incluidas sus temperaturas, bombas y cargas forzadas.

También se admiten las temperaturas actual/objetivo de la caldera y los
acumuladores, además de las temperaturas de fuente y demanda del controlador
Neo-HV cuando estén disponibles. Los canales históricos opcionales (oxígeno,
retorno, presión, existencias de pellets y humedad) aún no se crean como entidades.

Todavía no se crean varios depósitos de inercia porque no conocemos su esquema
de numeración en la API.

## Instalación

### HACS

1. Abrir **HACS → Integraciones**.
1. Elegir **Repositorios personalizados** en el menú de tres puntos.
1. Añadir `https://github.com/m4c3/hass-hargassner-cloud` como
   **Integración**.
1. Instalar **Hargassner Cloud** y reiniciar Home Assistant.
1. Abrir **Ajustes → Dispositivos y servicios → Añadir integración**.

### Instalación manual

Copiar `custom_components/hargassner_cloud` al directorio `custom_components`
de Home Assistant, reiniciar Home Assistant y añadir la integración desde la
interfaz.

## Configuración y opciones

La configuración solicita el correo y la contraseña de la cuenta Hargassner.
La URL predeterminada es `https://web.hargassner.at`. Si hay varias
instalaciones, se muestra una selección.

Las opciones permiten cambiar el intervalo de actualización (300 segundos de
forma predeterminada, mínimo 30), el área sugerida y las asignaciones JSON. Al
guardar se recarga automáticamente la integración.

## Autenticación

La integración obtiene las credenciales públicas del cliente web desde la
página de acceso actual de Hargassner. El repositorio no incorpora ningún
secreto público. La contraseña solo se envía a la URL Hargassner configurada.

Una contraseña rechazada inicia la reautenticación estándar. Un cambio
incompatible del portal crea un aviso de Reparaciones en lugar de pedir
incorrectamente una contraseña nueva.

## Diagnóstico y privacidad

Los diagnósticos contienen únicamente nombres de widgets y campos, tipos de
datos y un estado de API depurado. Se eliminan contraseñas, tokens, IDs de
instalación, valores operativos y URL de recursos. Revisa el archivo antes de
publicarlo.

## Solución de problemas

- **Error de autenticación:** comprobar la cuenta en
  [`web.hargassner.at`](https://web.hargassner.at).
- **Sin conexión:** comprobar el acceso HTTPS y posibles mantenimientos.
- **Entidades ausentes:** descargar los diagnósticos y comprobar widgets y
  campos; una asignación JSON puede adaptarlos.

## Licencia

El código y las ilustraciones originales están bajo la licencia MIT. Consulta
[LICENSE](LICENSE). Hargassner es una marca de su respectivo propietario.

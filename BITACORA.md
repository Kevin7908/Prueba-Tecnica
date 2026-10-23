# Bitácora

## 1. Herramienta de IA y para qué partes

**Herramienta:** Claude.

**Para qué la usé:**
- Para verificar posibles errores en la lectura del CSV.
- Con el estado en la base de datos.
- Para que el Excel no se corrompiera si algo fallaba a mitad de la escritura.
- Para que me explicara como funcionaba el dotenv y obviamente, para programar.

**Lo que hice yo:**
- Crear cada archivo con su código; Claude lo iba mejorando.
- Tomar las decisiones sobre qué hacer con los datos, por ejemplo si se descartaban y con qué reglas.
- Ya había usado pandas antes, pero no recordaba la sintaxis, así que lo lógico era guiarme con Claude para eso.
- Revisar el codigo que me daba y el porque se hacia de esa forma y no de otra, es mas en un momento le pregunte si habia otra forma de recorrer todos los datos que fuera mas optima y en que casos se podria aplicar. 

## 2. Prompts que me sirvieron

**1. Revisar la lectura del CSV**

Estoy leywndo un archivo csv con pandas u quiero asegurarme de que todo lo que estoy ahciendo esta bien este es mi codigo [aquí pegué el código de `lector.py`], revisalo y dime que errores podrian ocurrir qye no haya visto para cada posible erorr explicame como deberia solucionar y el porque de esa solucion teniendo en cuenta de que la app debe seguir funcionando asi algo falle

**2. Estado durante el proceso**

Tengo un codifo que lo que hace es prosecar como los registror de un .csv y en este momento lo guarda en la base de datos ahota mi prblea es que quierp menejar etados para sber en que moemento ocurre u error y en que dato por asi ecirlo con todo el contexto que tenemos necesito de que me ayudes a hacer todo bie estruturado lo que necesito que me ayudes es a actualizar el estadp durante el procesos sin dejar dañar ada evitar los duplicados explicae la logica que se podria implementar y dame el codigo para revisarlo.

**3. Que el Excel no se dañe si algo falla**

mi programa genera un repote en excel con openpyxl, pandas y se me paso por la cabeza que sucede si por ejemplo se apaga el computador o alguna cosa pasa mientras esta haciendo el excel o alfuna cosa asi, entonces quiero que todo sea seguro y que si algo pasa todo vuelva a ejecutarse bien

## 3. Algo que la IA me entregó mal o incompleto

 Al principio en la base de datos no se gaurdaba un dato (no recuerdo cual era) pero yo pensaba que no era de la base de datos si no que era de afuera, entonces en ese moemtno utilice chatgpt ya que tenia creditos gratis y en ese momento claude no tenia los creditos gratis (solo utilice chatgpt esa vez), y chat gpt empezo a alucinar a decirme no que era esto no que era que el dato no existia y cosas asi entonces revice un poquito (diria que fue suerte) y me percate de que el dato llegaba a la funcion pero yo no lo enviaba a la base de datos

Claude me agrego un pco mas de complejidad de lo necesario para este reto: un `@dataclass`, como no las exigía el enunciado y yo tenía que poder explicar cada línea, las quité y me quedé con lo mínimo. 


## 4. Qué decidí yo sin consultarle

- Antes de empezar con el proyecto ya sabia que iba a utilizar pandas.
- Escribi una base de codigo para que despues Claude corrigiera.
- Decidi las cosas como que se iba a descartar y esas cosas.
- Pensaba utilizar Docker, pero como era todo muy sencillo y facil de ejecutar, entonces mejor no lo utilice.
- Estructura del proyecto que todo estuviera desacoplado.

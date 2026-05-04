# Nombre del Proyecto: SCORBOT VISION CONTROLLER.



##### Objetivo: 

Implementar una aplicación escrita con lenguaje Python que integre una manera de controlar por visión de manera autónoma los brazos robóticos SCORBOT V+ y SCORBOT IX. Para procedimientos de pick and place de objetos pequeños en una mesa.

##### 

##### Requerimientos del proyecto:

###### 

###### Fase 1:

* Comunicación por puerto serial RS232 por medio de adaptador USB.
* Ventana de la aplicación de mínimo 1280x720p con tamaño adaptable
* GUI simple y funcional que permita operar el SCORBOT, debe ser responsive y que se vean todos los componentes. (Tkinter)
* Elemento de la GUI: Un panel de conexión que muestre el estado de conexión con el robot y botones para conectar y desconectar, además de un temporizador de sesión activa.
* Elemento de la GUI: Un panel de Terminal que muestre los comandos enviados hacia el SCORBOT y las respuestas enviadas del SCORBOT hacia el programa.
* Elemento de la GUI: Un botón de guardado del log de la terminal y otro botón para limpiar el texto de la terminal.
* Elemento de la GUI: Un panel de entrada de terminal que sirva para escribir comandos ACL para enviar al SCORBOT.
* Elemento de la GUI: Un botón para enviar y ejecutar los comandos ACL escritos en el panel de entrada por medio del puerto serial y un botón que sirva para enviar el aborto de emergencia hacia el controlador del robot.
* Elemento de la GUI: Un panel que haga streaming de video de la cámara del robot, que sea ajustable a cualquier tamaño de resolución.
* Elemento de la GUI: Un apartado de botones que contengan: 

&#x09;\* Alguna manera de seleccionar cual cámara es la que se quiere mostrar en el video.

&#x09;\* Un Botón para encender la cámara (Por defecto la Cámara debe comenzar apagada).

&#x09;\* Un Botón para apagar la cámara.

* Elemento de la aplicación: Un apartado de menú de configuraciones para la aplicación para adaptarse a las preferencias del usuario o para implementar herramientas de desarrollo como un modo "Mocking".

###### 

###### Fase 2:

* Visión del Robot: Por medio de la visión por computadora, se debe lograr establecer una zona de trabajo del robot y el reconocimiento de piezas y figuras.
* Visión del Robot: Por medio de visión por computadora, se debe establecer la posición de las figuras para que el robot se mueva hacia ellas.
* Se desea implementar una secuencia en ACL que sirva para moverse a una posición fija elevada desde la cual se pueda ver la totalidad del espacio de trabajo del robot, desde dónde se establezca la posición de los objetos y relacionar sus coordenadas de imagen con distancias de movimiento en el robot
* Se está evaluando el uso de stickers tipo QR llamados "Arucos", los cuales se usarían para identificar de manera más sencilla y rápida las posiciones de los objetos y su orientación en el plano.
* El Resto de la Implementación de la Fase 2 sigue en proceso de investigación y todas las funciones de movilidad del robot aún deben ser creadas e investigadas. La Fase 2 Está mas que nada en una etapa conceptual y nos apoyaremos de diversas tesis, trabajos, y manuales para realizar su implementación completa.



###### Fase 3:

* Para la Fase 3, se buscará realizar los últimos ajustes de detalles menores y mejoras en la UX.
* Se evaluará si es necesario un cambio de estructura.
* Idealmente se evaluará la implementación de ttk Bootstrap para modernizar la interfaz. Pero en su defecto se puede cambiar por un framework mas completo con otra arquitectura.



##### Pasos a Seguir:



1\. Implementar La interfaz gráfica de la fase 1, en la cual la prioridad es la funcionalidad sobre la estética. Es decir se debe lograr primordialmente la comunicación funcional con el controlador del SCORBOT.


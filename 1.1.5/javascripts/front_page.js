
var typewriter = false;
document$.subscribe((event) => {
    d = document.getElementById("typewriter");
    if ((d == null) || (d.innerHTML != "Speak QUA to ...")){
      return
    }
    typewriter = new Typewriter("#typewriter", {
        loop: true,
        delay: 75,
      });
      
    typewriter
    .pauseFor(2500)
    .typeString('Speak quantum to...')
    .pauseFor(3000)
    .deleteChars(13)
    .typeString('<strong>QUA</strong> to ')
    .typeString('<span style="color: #3082CF;">NV centers</span>')
    .pauseFor(5000)
    .deleteChars(10)
    .typeString('<span style="color: #3082CF;">transmons</span>')
    .pauseFor(5000)
    .deleteChars(9)
    .typeString('<span style="color: #3082CF;">atoms</span>')
    .pauseFor(5000)
    .deleteChars(5)
    .typeString('<span style="color: #3082CF;">ions</span>')
    .pauseFor(5000)
    .deleteChars(4)
    .typeString('<span style="color: #3082CF;">quantum dots</span>')
    .pauseFor(5000)
    .start();
  });
  

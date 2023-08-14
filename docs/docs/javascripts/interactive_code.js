
	
function genRandomString(length) {
  var chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  var charLength = chars.length;
  var result = '';
  for ( var i = 0; i < length; i++ ) {
     result += chars.charAt(Math.floor(Math.random() * charLength));
  }
  return result;
}

let tokenForInteractiveCode = genRandomString(15);
var interactiveKernelInitialized = false;

function initInteractiveCells(){
   var allCode = document.getElementsByTagName("pre");
       for (var i=0; i<allCode.length; i+= 1){
           if (window.getComputedStyle(allCode[i]).getPropertyValue("display") == "block" || window.getComputedStyle(allCode[i]).getPropertyValue("display") == "flow-root"){
               allCode[i].dataset.executable = "true";
               allCode[i].dataset.language = "python";
           }   
       }
   
       // thebelab.events.on("request-kernel")((kernel) => {
       //     // Find any cells with an initialization tag and ask Thebe to run them when ready
       //     console.log("TEST THIS");
       //     console.log(CodeToExecuteOnKernelLoad);
       //     kernel.requestExecute({code: "="});  // write configuration
       //     console.log("EXECUTING FOLLOWING CODE ")
       // });
   
       thebelab.bootstrap({
           requestKernel: true,
           mountActivateWidget: true,
           mountStatusWidget: true,
           useJupyterLite: false,
           useBinder: false,
           serverSettings: {
             baseUrl: 'http://localhost:8888',
             token: tokenForInteractiveCode
           }
       })
   
     }


function startInteractive(e){
   if (interactiveKernelInitialized){
       initInteractiveCells()
   }
   else{
   Swal.fire({
       title: '<strong>Connect to your local OPX</strong>',
       icon: 'success',
       html:
         'Please run following line from Python environment in which QUA is installed:<br><br>' +
         "<strong>jupyter lab --NotebookApp.token="+tokenForInteractiveCode+" --NotebookApp.allow_origin='*' --no-browser</strong>",
       showCloseButton: true,
       showCancelButton: true,
       focusConfirm: true,
       confirmButtonText:
         '<div class=".md-button .md-button--primary "> Done!</div>',
       confirmButtonAriaLabel: 'Proceed with connection to Jupyter server',
       cancelButtonText:
         '<div class="md-button">Cancel</div>',
       cancelButtonAriaLabel: 'Do not connect to Jupyter server'
     }).then((result)=> {
       if (result.isConfirmed){
           interactiveKernelInitialized  = true;
           initInteractiveCells()
       }
   })
   }

   }

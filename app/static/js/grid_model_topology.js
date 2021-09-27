// Constants
const ASSET_TYPE_NAME = 'asset_type_name';
const BUS = "bus";
// UUID to Drawflow Id Mapping
// const nodeToDbId = { 'bus': [], 'asset': [] };
const nodesToDB = new Map();


// Initialize Drawflow
const id = document.getElementById("drawflow");
const editor = new Drawflow(id);
editor.reroute = true;
editor.start();
// editor.drawflow.drawflow.Home.data; // All node level data are saved here

/* Mouse and Touch Actions */
var elements = document.getElementsByClassName('drag-drawflow');
for (let i = 0; i < elements.length; i++) {
    elements[i].addEventListener('touchend', drop, false);
    elements[i].addEventListener('touchstart', drag, false);
}
var elements = document.getElementsByClassName('section__component');
for (let i = 0; i < elements.length; i++) {
    elements[i].addEventListener('touchend', drop, false);
    elements[i].addEventListener('touchstart', drag, false);
}
function allowDrop(ev) {
    ev.preventDefault();
}

function drag(ev) {
    ev.dataTransfer.setData("node", ev.target.getAttribute('data-node'));
}

function drop(ev) {
    ev.preventDefault();
    const nodeName = ev.dataTransfer.getData("node");
    (nodeName === BUS) ? IOBusOptions(nodeName, ev.clientX, ev.clientY)
        : addNodeToDrawFlow(nodeName, ev.clientX, ev.clientY);
}


function IOBusOptions(nodeName, posX, posY) {
    const checkMinMax = (value, min, max) => (value <= min) ? min : (value >= max) ? max : value;
    Swal.mixin({
        input: 'number',
        confirmButtonText: 'Next',
        showCancelButton: true,
        progressSteps: ['1', '2']
    })
        .queue([
            {
                title: 'Bus Inputs',
                text: 'Provide the number of bus Inputs (default 1)',
            },
            {
                title: 'Bus Outputs',
                text: 'Provide the number of bus Outputs (default 1)',
            }
        ])
        .then((result) => {
            if (result.value) {
                const inputs = checkMinMax(result.value[0], 1, 7);
                const outputs = checkMinMax(result.value[1], 1, 7);
                addNodeToDrawFlow(nodeName, posX, posY, inputs, outputs);
            }
        })
}


// Disallow Any Connection to be created without a bus.
editor.on('connectionCreated', function (connection) {
    var nodeIn = editor.getNodeFromId(connection['input_id']);
    var nodeOut = editor.getNodeFromId(connection['output_id']);
    if ((nodeIn['name'] !== BUS && nodeOut['name'] !== BUS) || (nodeIn['name'] === BUS && nodeOut['name'] === BUS)) {
        editor.removeSingleConnection(connection['output_id'], connection['input_id'], connection['output_class'], connection['input_class']);
        Swal.fire('Unexpected Connection', 'Please connect assets to each other\n only through a bus node. Interconnecting busses is also not allowed.', 'error')
    }
})

// might be redundant
editor.on('nodeCreated', function (nodeID) {
    // region bind installed_capacity to age_installed Changes
    // const nodeIdInstalledCapInput = document.getElementById(`node-${nodeID}`).querySelector("input[name='installed_capacity']");
    // if (nodeIdInstalledCapInput) {
    //     nodeIdInstalledCapInput.addEventListener('change', function (e) {
    //         const ageInstalledElement = e.target.closest("#FormGroup").querySelector("input[name='age_installed']");
    //         if (e.target.value === '0') {
    //             ageInstalledElement.value = '0';
    //             ageInstalledElement.readOnly = true;
    //             let notifyAgeInputEvent = new Event("input", { bubbles: true });
    //             ageInstalledElement.dispatchEvent(notifyAgeInputEvent);
    //         } else
    //             ageInstalledElement.readOnly = false;
    //     });
    //     // for existing nodes check if installed cap is zero and set age_installed to read only
    //     if (nodeIdInstalledCapInput.value === '0')
    //         nodeIdInstalledCapInput.closest("#FormGroup").querySelector("input[name='age_installed']").readOnly = true;
    // }
    // endregion
})

editor.on('nodeRemoved', function (nodeID) {
    // remove nodeID from nodesToDB
    nodesToDB.delete('node-'+nodeID);
})


async function addNodeToDrawFlow(name, pos_x, pos_y, nodeInputs = 1, nodeOutputs = 1, nodeData = {}) {
    if (editor.editor_mode === 'fixed')
        return false;
    pos_x = pos_x * (editor.precanvas.clientWidth / (editor.precanvas.clientWidth * editor.zoom)) - (editor.precanvas.getBoundingClientRect().x * (editor.precanvas.clientWidth / (editor.precanvas.clientWidth * editor.zoom)));
    pos_y = pos_y * (editor.precanvas.clientHeight / (editor.precanvas.clientHeight * editor.zoom)) - (editor.precanvas.getBoundingClientRect().y * (editor.precanvas.clientHeight / (editor.precanvas.clientHeight * editor.zoom)));
    return createNodeObject(name, nodeInputs, nodeOutputs, {}, pos_x, pos_y);
}

// region Show Modal either by double clicking the box or the drawflow node.
var transform = '';

document.addEventListener("dblclick", function (e) {
    const openModal = function (box) {
        box.closest(".drawflow-node").style.zIndex = "9999";
        box.querySelector('.modal').style.display = "block";
        transform = editor.precanvas.style.transform;
        editor.precanvas.style.transform = '';
        editor.precanvas.style.left = editor.canvas_x + 'px';
        editor.precanvas.style.top = editor.canvas_y + 'px';
        editor.editor_mode = "fixed";
    }

    const closestNode = e.target.closest('.drawflow-node');
    const nodeType = closestNode.querySelector('.box').getAttribute(ASSET_TYPE_NAME);
    if (closestNode && closestNode.querySelector('.modal').style.display !== "block") {
        const topologyNodeId = closestNode.id;
        const getUrl = formGetUrl + nodeType +
            (nodesToDB.has(topologyNodeId) ? "/" + nodesToDB.get(topologyNodeId).uid : "");
        fetch(getUrl)
        .then(res=>res.text())
        .then(res=> {
            const formParentDiv = closestNode.querySelector('form').parentNode;
            // console.log(formParentDiv);
            formParentDiv.innerHTML = res;
            const box = formParentDiv.closest('.box');
            openModal(box);
        })
        .catch(err => console.log("Modal get form JS Error: " + err));
    }
});
>>>>>>> 85f7ba7... First translation draft of topology
// endregion
}),editor.on("nodeRemoved",function(a){// remove nodeID from nodesToDB
nodesToDB.delete("node-"+a)});async function addNodeToDrawFlow(a,b,c,d=1,e=1,f={}){return"fixed"!==editor.editor_mode&&(b=b*(editor.precanvas.clientWidth/(editor.precanvas.clientWidth*editor.zoom))-editor.precanvas.getBoundingClientRect().x*(editor.precanvas.clientWidth/(editor.precanvas.clientWidth*editor.zoom)),c=c*(editor.precanvas.clientHeight/(editor.precanvas.clientHeight*editor.zoom))-editor.precanvas.getBoundingClientRect().y*(editor.precanvas.clientHeight/(editor.precanvas.clientHeight*editor.zoom)),createNodeObject(a,d,e,{},b,c));// the following translation/transformation is required to correctly drop the nodes in the current clientScreen
}// region Show Modal either by double clicking the box or the drawflow node.
var transform="";document.addEventListener("dblclick",function(a){var b=this;const c=function(a){a.closest(".drawflow-node").style.zIndex="9999",a.querySelector(".modal").style.display="block",transform=editor.precanvas.style.transform,editor.precanvas.style.transform="",editor.precanvas.style.left=editor.canvas_x+"px",editor.precanvas.style.top=editor.canvas_y+"px",editor.editor_mode="fixed"},d=a.target.closest(".drawflow-node"),e=d.querySelector(".box").getAttribute(ASSET_TYPE_NAME);if(d&&"block"!==d.querySelector(".modal").style.display){const a=d.id,f=formGetUrl+e+(nodesToDB.has(a)?"/"+nodesToDB.get(a).uid:"");fetch(f).then(function(a){return _newArrowCheck(this,b),a.text()}.bind(this)).then(function(a){_newArrowCheck(this,b);const e=d.querySelector("form").parentNode;// console.log(formParentDiv);
e.innerHTML=a;const f=e.closest(".box");c(f)}.bind(this)).catch(function(a){return _newArrowCheck(this,b),console.log("Modal get form JS Error: "+a)}.bind(this))}});// endregion
// region close Modal on: 1. click 'x', 2. press 'esc' and 3. click outside the modal.
function closeModalSteps(a){// // Change the name of the node based on input
const b=a.closest(".drawflow_content_node").querySelector(".nodeName");// End name change
// hide the modal
// bring node to default z-index
// delete modal form
b.textContent=`${a.querySelector("input[df-name]").value}`,a.style.display="none",a.closest(".drawflow-node").style.zIndex=a.closest(".drawflow-node").classList.contains("ess")?"1":"2",editor.precanvas.style.transform=transform,editor.precanvas.style.left="0px",editor.precanvas.style.top="0px",editor.editor_mode="edit",a.querySelector("form").parentNode.innerHTML="<form></form>"}const closemodal=function(a){return _newArrowCheck(this,_this3),closeModalSteps(a.target.closest(".modal"))}.bind(void 0),submitForm=function(a){var b=this;_newArrowCheck(this,_this3);const c=a.target.closest(".modal-content").querySelector("form"),d=c.closest(".box").getAttribute(ASSET_TYPE_NAME),e=c.closest(".drawflow-node").id,f=e.split("-").pop(),g=formPostUrl+d+(nodesToDB.has(e)?"/"+nodesToDB.get(e).uid:""),h=new FormData(c),i=editor.drawflow.drawflow.Home.data[f].pos_x,j=editor.drawflow.drawflow.Home.data[f].pos_y;if(h.set("pos_x",i),h.set("pos_y",j),d===BUS){const a=Object.keys(editor.drawflow.drawflow.Home.data[f].inputs).length,b=Object.keys(editor.drawflow.drawflow.Home.data[f].outputs).length;h.set("input_ports",a),h.set("output_ports",b)}fetch(g,{method:"POST",headers:{// 'Content-Type': 'multipart/form-data', //'application/json', // if enabled then read json.loads(request.body) in the backend
"X-CSRFToken":csrfToken},body:h}).then(function(a){return _newArrowCheck(this,b),a.json()}.bind(this)).then(function(f){_newArrowCheck(this,b),f.success?(!1===nodesToDB.has(e)&&nodesToDB.set(e,{uid:f.asset_id,assetTypeName:d}),closeModalSteps(a.target.closest(".modal"))):c.innerHTML=f.form_html}.bind(this)).catch(function(a){return _newArrowCheck(this,b),console.log("Modal form JS Error: "+a)}.bind(this))}.bind(void 0);document.addEventListener("keydown",function(a){const b=document.getElementsByClassName("modal");if(27===a.keyCode){var c,d=_createForOfIteratorHelper(b);try{for(d.s();!(c=d.n()).done;){let a=c.value;"block"===a.style.display&&closeModalSteps(a)}}catch(a){d.e(a)}finally{d.f()}}}),window.onclick=function(a){const b=document.getElementsByClassName("modal");var c,d=_createForOfIteratorHelper(b);try{for(d.s();!(c=d.n()).done;){const b=c.value;a.target===b&&"block"===b.style.display&&closeModalSteps(b)}}catch(a){d.e(a)}finally{d.f()}};// endregion set
async function createNodeObject(a,b=1,c=1,d={},e,f){const g="undefined"==typeof d.name?a:d.name,h=`<div class="box" ${ASSET_TYPE_NAME}="${a}">
        <div class="modal" style="display:none">
          <div class="modal-content">
            <span class="close" onclick="closemodal(event)">&times;</span>
            <br>
            <h2 class="panel-heading" text-align: left">${a.replaceAll("_"," ")} Properties</h2>
            <br>
            <div class="row">
            <div class="col-md-1"></div>
            <div class="col-md-10">
                <form></form>
            </div>
            </div>
            <br>
            <div class="row">
                <div class="col-md-3"></div>
                <div class="col-md-6">
                ${scenarioBelongsToUser?"<button class=\"modalbutton\" style=\"font-size: medium; font-family: century gothic\" onclick=\"submitForm(event)\">Ok</button>":""}
                </div>
            </div>
          </div>
        </div>
    </div>
    <div class="nodeName" >${g}</div>`;return{editorNodeId:editor.addNode(a,b,c,e,f,a,d,h),specificNodeType:a}}
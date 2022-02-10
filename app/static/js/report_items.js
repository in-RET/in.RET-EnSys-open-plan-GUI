function addReportItemGraphToDOM(parameters, reportDOMId="report_items"){

// todo: use DOMsanitize to counter XSS

    const graphID = parameters.graph_id + "_plot";

    // generate html elements of a graph area
    var newReportItemDOM = ml("div", { id: parameters.graph_id, class: "chart", style: "height: fit-content;"}, [
            ml("div", { class: "chart__header"}, [
                ml("div", {}, [
                    ml("span", { class: "title"}, parameters.title)
                ]),
                ml("div", { class: "dropdown"}, [
                    ml("button", { class: "btn dropdown-toggle btn--transparent", type: "button", id: "dropdownMenuTS", 'data-bs-toggle': "dropdown", 'aria-expanded': "false"}, [
                       ml("span", { class: "icon icon-more"}, [])
                    ]),
                    ml("ul", { class: "dropdown-menu", 'aria-labelledby': "dropdownMenuTS"}, [
                        ml("li", { class: "dropdown-item"}, ml("a", {href: urlNotImplemented}, "Export as .xls")),
                        ml("li", { class: "dropdown-item"}, ml("a", {href: urlNotImplemented}, "Export as .pdf")),
                        ml("li", { class: "dropdown-item"}, ml("a", {href: urlCopyReportItem}, "Copy item")),
                        ml("li", { class: "dropdown-item"}, ml("a", {href: urlDeleteReportItem}, "Delete item")),
                    ]),
                ]),
            ]),
            ml("div", { class: "chart__plot"}, ml("div", {id: graphID}, [])),
        ]
    );

    // append the graph to the DOM
    document.getElementById(reportDOMId).appendChild(newReportItemDOM);

    return graphID

};

// credits: https://idiallo.com/javascript/create-dom-elements-faster
function ml(tagName, props, nest) {
    var el = document.createElement(tagName);
    if(props) {
        for(var name in props) {
            if(name.indexOf("on") === 0) {
                el.addEventListener(name.substr(2).toLowerCase(), props[name], false)
            } else {
                el.setAttribute(name, props[name]);
            }
        }
    }
    if (!nest) {
        return el;
    }
    return nester(el, nest)
}

// credits: https://idiallo.com/javascript/create-dom-elements-faster
function nester(el, n) {
    if (typeof n === "string") {
        var t = document.createTextNode(n);
        el.appendChild(t);
    } else if (n instanceof Array) {
        for(var i = 0; i < n.length; i++) {
            if (typeof n[i] === "string") {
                var t = document.createTextNode(n[i]);
                el.appendChild(t);
            } else if (n[i] instanceof Node){
                el.appendChild(n[i]);
            }
        }
    } else if (n instanceof Node){
        el.appendChild(n)
    }
    return el;
}

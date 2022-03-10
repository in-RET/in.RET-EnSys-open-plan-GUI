    function submitModalForm(event, modalId=""){
        const submitFormBtn = document.getElementById(modalId + "SubmitBtn");
        submitFormBtn.click();
    }


    function showModal(event, modalId="", url=null){
        // update the url linked to the form
        var modalInstance = $("#" + modalId);
        console.log(modalInstance);
        console.log(modalId);
        console.log(url);
        if(url){
            modalInstance.find('.modal-body form').attr("action", url);
        }

         modalInstance.modal("show")
    }
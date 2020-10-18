$(document).ready(function(){
    

    $('#files').change(function(){
        $('fileinfo').html("");
        var myfiles = $(this).prop('files');
        for(var i = 0; i < myfiles.length; i++){
            $('#fileinfo').append("<br><h5 class='p-1'>"+myfiles[i].name+'</h5>');
        }
    });

    $('#home').click(function(){
        console.log('ok');
        window.location.href = 'http://127.0.0.1:5000/';
    });

});

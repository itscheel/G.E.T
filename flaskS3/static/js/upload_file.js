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

    $('body').on('click','img',async  function(){
        var $img = $(this);
        var id = $img.attr("id");
        console.log('id:'+id);
        $('#id').val(id)
        console.log('id:'+id+'val:'+$('#id').val(id));
        deletefile(id,'/delete');
    })

    function deletefile(name, path){
        event.preventDefault();
        console.log('post delete');
        $.ajax({
            url: path,
            data : $('form').serialize(),
            type: 'POST',
            success: function(response){

                console.log('response:'+response);
                window.location.href = 'http://127.0.0.1:5000/files';

            },
            error: function(error){
                console.log("Error: "+error);
            }
        });
    }

});

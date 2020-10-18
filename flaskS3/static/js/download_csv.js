$(document).ready(function(){


    $('#form').submit(function(){
        get_data('/','');
    });

    $('#submit').click(function(){
        get_data('','/set_ajax');
    });

    $('#home').click(function(){
        console.log('ok');
        window.location.href = 'http://127.0.0.1:5000/';
    });
    function loaftable(DatosJson){
        
        console.log(Object.keys(DatosJson));
        
        for (i = 0; i < DatosJson.length; i++){
            if(i==0){
                $("#form").after(
                    "<div class='container-fluid'>"+
                        "<div class='row'>"+
                                "<div clas='col-8'>"+
                                    "<table class='table'>" + 
                                        '<thead>' + 
                                            '<th>Documento</th>'+
                                            '<th>Fecha</th>'+
                                            '<th>Unidades en las que se mide</th>'+
                                            '<th>Caja y bancos</th>'+
                                            '<th>Total activos</th>'+
                                            '<th>Total pasivos</th>' + 
                                            '<th>Total pratimonio</th>' + 
                                            '<th>Ventas</th>' + 
                                            '<th>Costo de ventas</th>' +
                                            '<th>Utilidad bruta</th>' + 
                                            '<th>Utilidad operacional</th>'+ 
                                            '<th>Utilidad antes de impuestos</th>'+
                                            '<th>Utilidad neta</th>'+
                                        '</thead>'+
                                        "<tbody id='bod'>"+
                                        '</tbody>'+
                                    '</table>'+
                                '</div>'+
                            '</div>'+
                    "</div>");
            }   
    
            $("#bod").append('<tr>' + 
                                '<td align="center" style="dislay: none;">' + DatosJson[i]['Archivo'] + '</td>'+
                                '<td align="center" style="dislay: none;">' + DatosJson[i]['Fecha'] + '</td>'+
                                '<td align="center" style="dislay: none;">' + DatosJson[i]['Unidades en las que se mide'] + '</td>'+
                                '<td align="center" style="dislay: none;">' + DatosJson[i]['Caja y bancos'] + '</td>'+
                                '<td align="center" style="dislay: none;">' + DatosJson[i]['Total activos'] + '</td>'+
                                '<td align="center" style="dislay: none;">' + DatosJson[i]['Total pasivo'] + '</td>'+
                                '<td align="center" style="dislay: none;">' + DatosJson[i]['Total patrimonio'] + '</td>'+
                                '<td align="center" style="dislay: none;">' + DatosJson[i]['Ventas'] + '</td>'+
                                '<td align="center" style="dislay: none;">' + DatosJson[i]['Costo de ventas'] + '</td>'+
                                '<td align="center" style="dislay: none;">' + DatosJson[i]['Utilidad bruta'] + '</td>'+
                                '<td align="center" style="dislay: none;">' + DatosJson[i]['Utilidad operacional'] + '</td>'+
                                '<td align="center" style="dislay: none;">' + DatosJson[i]['Utilidad antes de impuestos'] + '</td>'+
                                '<td align="center" style="dislay: none;">' + DatosJson[i]['Utilidad neta'] + '</td>'+
                            '</tr>');
        
        }

        
        
    }

    

    function get_data(name, path){
        event.preventDefault();
        $.ajax({
            url: path,
            data : $('form').serialize(),
            type: 'POST',
            success: function(response){

                var consult = JSON.parse(response);
                loaftable(consult);
                $('#pdftable').hide();
                console.log(consult);

            },
            error: function(error){
                console.log("Error: "+error);
            }
        });
    }

    

});
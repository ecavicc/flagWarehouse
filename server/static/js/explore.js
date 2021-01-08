// Table
let table = $('#table');
table.bootstrapTable({loadingFontSize: '1rem'});
$(function () {
    $(document).on('click', '#refresh', function () {
        table.bootstrapTable('showLoading');
        $.ajax({
            url: '/explore/get_flags',
            method: 'get',
            data: {
                exploit_name: $('#exploit_name_select').val(),
                username: $('#username_select').val(),
                team_ip: $('#team_ip_select').val(),
                since: $('#since_datetime').val().replace('T', ' '),
                until: $('#until_datetime').val().replace('T', ' '),
                status: $('#status_select').val(),
                server_response: $('#response_select').val()
            },
            dataType: 'json',
            success: function (response) {
                table.bootstrapTable('load', response);
                table.bootstrapTable('hideLoading');
            }
        });
    });
});


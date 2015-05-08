    $(function() {
      $('a#calculate').bind('click', function() {
        $.getJSON('/_add_numbers', {
          a: $('input[name="a"]').val(),
          b: $('input[name="b"]').val()
        }, function(data) {
          $("#result").text(data.result);
        });
        return false;
      });
    });

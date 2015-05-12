$(document).ready(function() {
    // by defallut loat a dashlet
    $("#dashletContent").load("/ntimeline");
     var defaultname = $("#menuList li.selected").find("a").html();
      $("#selectedCrumb").html(defaultname);
    $("#menuList .menuItem").on("click", function() {
        $(this).addClass("selected").siblings().removeClass("selected");
        var page = $(this).attr("data-item");
        var crumbname = $(this).find("a").html();
        $("#dashletContent").load(page, function() {
            $("#selectedCrumb").html(crumbname);
        });
    });
});
